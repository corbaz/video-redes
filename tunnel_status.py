#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chequeo del estado del backend residencial (app local + túnel + Railway)."""

import os
import socket

import requests

LOCAL_PORT = int(os.environ.get('PORT', '8000'))
RAILWAY_URL = os.environ.get('RAILWAY_URL', 'https://redes-download.up.railway.app')
_URL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tunnel_url')


def _app_local_up():
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect(('127.0.0.1', LOCAL_PORT))
        return True
    except Exception:
        return False
    finally:
        s.close()


def _current_url():
    try:
        return open(_URL_FILE, encoding='utf-8').read().strip()
    except Exception:
        return ''


def _tunnel_up(url):
    if not url:
        return False
    try:
        requests.get(url, timeout=8)
        return True
    except Exception:
        return False


def main():
    print('=' * 44)
    print('  Estado del backend residencial')
    print('=' * 44)

    app = _app_local_up()
    print(f'App local (localhost:{LOCAL_PORT}): {"ARRIBA" if app else "ABAJO"}')

    url = _current_url()
    print(f'URL del tunel: {url or "(ninguna)"}')

    tun = _tunnel_up(url)
    print(f'Tunel responde: {"SI" if tun else "NO"}')

    # Prueba real: extraer un post de Threads por Railway (debe reenviar a casa).
    ok = False
    try:
        r = requests.post(RAILWAY_URL.rstrip('/') + '/api/extract',
                          json={'url': 'https://www.threads.com/@mardelplataweb/post/DarzR2gkt7P'},
                          timeout=90)
        ok = r.json().get('success', False)
    except Exception:
        ok = False
    print(f'Prueba Threads via Railway: {"OK (reenvio funciona)" if ok else "FALLA"}')

    print('-' * 44)
    if app and tun and ok:
        print('TODO OK: el backend de casa esta operativo.')
    elif not app:
        print('La app local no esta corriendo. Ejecuta tunnel.bat')
    elif not tun:
        print('El tunel no responde. Ejecuta tunnel.bat (se auto-reinicia solo).')
    else:
        print('App y tunel OK, pero el reenvio falla. Revisa ADMIN_SECRET / logs.')


if __name__ == '__main__':
    main()
