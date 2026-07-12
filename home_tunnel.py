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
    print("❌ No encuentro cloudflared. Instalalo: winget install Cloudflare.cloudflared")
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
        print(f"{'✅' if ok else '❌'} Registro en Railway: {r.status_code}")
        return ok
    except Exception as e:
        print(f"⚠️ No se pudo registrar en Railway: {e}")
        return False


def main():
    secret = ADMIN_SECRET or input("Clave admin (ADMIN_SECRET): ").strip()
    globals()['ADMIN_SECRET'] = secret

    cloudflared = _find_cloudflared()
    print(f"🚇 Abriendo túnel hacia http://localhost:{LOCAL_PORT} ...")
    proc = subprocess.Popen(
        [cloudflared, 'tunnel', '--url', f'http://localhost:{LOCAL_PORT}'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',
    )

    public_url = None
    # Leer la salida hasta capturar la URL pública.
    for line in proc.stdout:
        m = _URL_RE.search(line)
        if m:
            public_url = m.group(0)
            print(f"\n🌐 URL pública: {public_url}\n")
            break

    if not public_url:
        print("❌ No se capturó la URL del túnel. Revisá cloudflared.")
        proc.terminate()
        sys.exit(1)

    register(public_url)
    print("Listo. Dejá esta ventana abierta. (Ctrl+C para cortar)\n")

    # Heartbeat: re-registrar cada tanto y vigilar que el túnel siga vivo.
    try:
        last = time.time()
        while True:
            if proc.poll() is not None:
                print("⚠️ cloudflared se cerró. Salgo.")
                break
            if time.time() - last >= HEARTBEAT_SECONDS:
                register(public_url)
                last = time.time()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nCortando túnel...")
    finally:
        proc.terminate()


if __name__ == '__main__':
    main()
