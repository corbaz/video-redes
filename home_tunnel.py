#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backend residencial: abre el túnel Cloudflare hacia la app local y le avisa
la URL a Railway para que reenvíe el contenido con login.

Corre en TU PC (IP residencial). Flujo:
  1. Lanza `cloudflared tunnel --url http://localhost:<port>` y captura la URL
     pública (https://xxx.trycloudflare.com).
  2. La registra en Railway (POST /api/admin/set-fallback con ADMIN_SECRET).
  3. La re-registra cada 2 min (heartbeat), por si Railway reinicia.
  4. Si cloudflared se cae, lo reinicia y actualiza la URL.

Requisitos: la app local ya escuchando en el puerto, y estas variables
(por entorno o editando los defaults de abajo):
  ADMIN_SECRET  -> la misma clave del panel admin de Railway
  RAILWAY_URL   -> https://redes-download.up.railway.app
"""

import os
import re
import sys
import time
import shutil
import subprocess

import requests

LOCAL_PORT = int(os.environ.get('PORT', '8000'))
RAILWAY_URL = os.environ.get('RAILWAY_URL', 'https://redes-download.up.railway.app')
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', '')
HEARTBEAT_SECONDS = 120
_URL_RE = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')


def _find_cloudflared():
    exe = shutil.which('cloudflared')
    if exe:
        return exe
    for base in (r'C:\Program Files (x86)\cloudflared', r'C:\Program Files\cloudflared'):
        candidate = os.path.join(base, 'cloudflared.exe')
        if os.path.isfile(candidate):
            return candidate
    print("[X] No encuentro cloudflared. Instalalo: winget install Cloudflare.cloudflared")
    sys.exit(1)


def register(url):
    """Avisa la URL a Railway. Devuelve True si quedó registrada."""
    try:
        r = requests.post(
            RAILWAY_URL.rstrip('/') + '/api/admin/set-fallback',
            json={'secret': ADMIN_SECRET, 'url': url},
            timeout=20,
        )
        ok = r.status_code == 200 and r.json().get('success')
        print(f"{'[OK]' if ok else '[X]'} Registro en Railway: {r.status_code}")
        return ok
    except Exception as e:
        print(f"[!] No se pudo registrar en Railway: {e}")
        return False


import threading

CHECK_SECONDS = 30           # cada cuánto verificar que el túnel siga vivo
_URL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tunnel_url')
_state = {'url': None}
_state_lock = threading.Lock()


def _write_url_file(url):
    try:
        with open(_URL_FILE, 'w', encoding='utf-8') as f:
            f.write(url or '')
    except Exception:
        pass


def _watch_cloudflared(proc):
    """Lee la salida de cloudflared y registra cada URL nueva que aparezca."""
    for line in proc.stdout:
        m = _URL_RE.search(line)
        if m:
            new_url = m.group(0)
            with _state_lock:
                changed = new_url != _state['url']
                _state['url'] = new_url
            if changed:
                print(f"\nURL pública: {new_url}")
                _write_url_file(new_url)
                register(new_url)


def _tunnel_alive(url):
    """Verifica que el túnel responda de verdad (no solo que cloudflared corra)."""
    if not url:
        return False
    try:
        requests.get(url, timeout=8)
        return True
    except Exception:
        return False


def _launch_cloudflared(cloudflared):
    print(f"Abriendo túnel hacia http://localhost:{LOCAL_PORT} ...")
    proc = subprocess.Popen(
        [cloudflared, 'tunnel', '--url', f'http://localhost:{LOCAL_PORT}'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
    )
    threading.Thread(target=_watch_cloudflared, args=(proc,), daemon=True).start()
    return proc


def _wait_for_url(proc, seconds=40):
    for _ in range(seconds * 2):
        with _state_lock:
            if _state['url']:
                return True
        if proc.poll() is not None:
            return False
        time.sleep(0.5)
    return False


def main():
    secret = ADMIN_SECRET or input("Clave admin (ADMIN_SECRET): ").strip()
    globals()['ADMIN_SECRET'] = secret

    cloudflared = _find_cloudflared()
    proc = _launch_cloudflared(cloudflared)
    if not _wait_for_url(proc):
        print("[X] No se capturó la URL del túnel. Revisá cloudflared.")
        proc.terminate()
        sys.exit(1)

    print("Listo. Dejá esta ventana abierta. (Ctrl+C para cortar)\n")

    fails = 0
    try:
        while True:
            time.sleep(CHECK_SECONDS)
            # ¿cloudflared murió? relanzarlo.
            if proc.poll() is not None:
                print("[!] cloudflared se cerró; relanzando...")
                with _state_lock:
                    _state['url'] = None
                proc = _launch_cloudflared(cloudflared)
                _wait_for_url(proc)
                fails = 0
                continue

            with _state_lock:
                url = _state['url']

            if _tunnel_alive(url):
                fails = 0
                register(url)  # renovar en Railway (por si reinició)
            else:
                fails += 1
                print(f"[!] El túnel no responde (intento {fails}/2)")
                if fails >= 2:
                    print("[!] Túnel muerto: reinicio cloudflared para una URL nueva...")
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    time.sleep(2)
                    with _state_lock:
                        _state['url'] = None
                    proc = _launch_cloudflared(cloudflared)
                    _wait_for_url(proc)
                    fails = 0
    except KeyboardInterrupt:
        print("\nCortando túnel...")
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
        _write_url_file('')


if __name__ == '__main__':
    main()
