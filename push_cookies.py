#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Login local -> empuja la cookie a Railway.

Corre EN TU MÁQUINA (IP residencial, en la que Instagram/Facebook confían, sin
el loop de captchas que aparece en Railway). Abre una ventana real de navegador,
esperás a que te loguees normalmente, captura las cookies de sesión y las manda
al panel /admin/cookies de tu app en Railway.

Uso:
    python push_cookies.py instagram
    python push_cookies.py facebook

Config (por variables de entorno o se piden por teclado):
    ADMIN_SECRET  -> la clave del panel admin (la misma de Railway)
    RAILWAY_URL   -> URL de la app (default: https://redes-download.up.railway.app)
"""

import os
import sys
import time
import argparse

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from common.browser_login import (  # noqa: E402
    cookies_to_netscape, AUTH_COOKIE_NAMES, LOGIN_TARGET_URLS,
)
from playwright.sync_api import sync_playwright  # noqa: E402

DEFAULT_RAILWAY_URL = 'https://redes-download.up.railway.app'
SETTLE_SECONDS = 2.5
MAX_WAIT_SECONDS = 600  # 10 min para loguearse tranquilo


def capture_cookies(platform: str):
    """Abre un navegador visible local, espera el login y devuelve las cookies."""
    required = AUTH_COOKIE_NAMES[platform]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # ventana visible = IP residencial
        context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_TARGET_URLS[platform])
        print(f"\n👉 Logueate en la ventana de {platform} que se abrió.")
        print("   Esperando a que completes el login...")

        deadline = time.time() + MAX_WAIT_SECONDS
        first_seen = None
        while time.time() < deadline:
            names = {c['name'] for c in context.cookies()}
            if all(n in names for n in required):
                if first_seen is None:
                    first_seen = time.time()
                elif time.time() - first_seen >= SETTLE_SECONDS:
                    cookies = context.cookies()
                    browser.close()
                    return cookies
            else:
                first_seen = None
            time.sleep(1)

        browser.close()
        raise TimeoutError("No se detectó el login a tiempo.")


def push_to_railway(netscape_cookies: str, url: str, secret: str):
    endpoint = url.rstrip('/') + '/api/admin/cookies'
    resp = requests.post(endpoint, json={'secret': secret, 'cookies': netscape_cookies}, timeout=30)
    return resp


def main():
    parser = argparse.ArgumentParser(description="Login local y push de cookies a Railway.")
    parser.add_argument('platform', choices=['instagram', 'facebook'])
    parser.add_argument('--url', default=os.environ.get('RAILWAY_URL', DEFAULT_RAILWAY_URL))
    parser.add_argument('--secret', default=os.environ.get('ADMIN_SECRET', ''))
    args = parser.parse_args()

    secret = args.secret or input("Clave del panel admin (ADMIN_SECRET): ").strip()
    if not secret:
        print("❌ Falta la clave admin.")
        sys.exit(1)

    try:
        cookies = capture_cookies(args.platform)
    except TimeoutError as e:
        print(f"❌ {e}")
        sys.exit(1)

    netscape = cookies_to_netscape(cookies)
    print(f"🍪 Cookie capturada ({len(cookies)} entradas). Enviando a {args.url}...")

    resp = push_to_railway(netscape, args.url, secret)
    if resp.status_code == 200 and resp.json().get('success'):
        print("✅ Cookie subida a Railway. Ya podés descargar el video desde la app.")
    else:
        print(f"❌ Railway respondió {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)


if __name__ == '__main__':
    main()
