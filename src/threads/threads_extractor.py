"""Extractor de Threads (Meta) vía navegador headless.

Threads no lo soporta yt-dlp y no expone el video en el HTML: lo carga con una
llamada GraphQL autenticada. Igual que hacen los servicios online, abrimos la
página en un Chromium real (con la cookie de Meta), y capturamos la URL del
video interceptando las respuestas de red.

Playwright se importa PEREZOSAMENTE: en Railway (sin Playwright) la extracción
falla con needs_remote=True y el servidor reenvía el pedido al backend
residencial (la PC de casa), que sí tiene Playwright + cookie + IP buena.
"""

import os
import re
import json
from typing import Dict, Any

from common.cookies_util import combined_cookies_file

# Claves de Meta que contienen URLs de video progresivo (.mp4).
_VIDEO_KEYS = ('browser_native_hd_url', 'browser_native_sd_url', 'video_url', 'progressive_url')
_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


def _unescape(u: str) -> str:
    try:
        return u.encode('utf-8').decode('unicode_escape').replace('\\/', '/')
    except Exception:
        return u.replace('\\/', '/')


class ThreadsExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            # Sin Playwright (ej. Railway): que el servidor reenvíe a la casa.
            # El texto NO debe contener frases de "login" para no disparar el
            # modal de cookies del frontend; el reenvío se activa por needs_remote.
            return {
                "success": False,
                "error": "Threads no está disponible ahora mismo. El servidor de descargas está apagado; probá de nuevo en un rato.",
                "needs_remote": True,
            }

        print(f"🔍 Extrayendo Threads con navegador: {url}")
        candidates = []  # (prioridad, url)

        def harvest(body: str):
            for key in _VIDEO_KEYS:
                for m in re.findall(r'"' + key + r'"\s*:\s*"([^"]+\.mp4[^"]*)"', body):
                    pr = 0 if 'hd' in key else 1
                    candidates.append((pr, _unescape(m)))
            # video_versions: lista con {"url": "...mp4..."}
            for block in re.findall(r'"video_versions"\s*:\s*\[(.*?)\]', body, re.S):
                for uu in re.findall(r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"', block):
                    candidates.append((2, _unescape(uu)))

        def on_response(resp):
            try:
                ct = resp.headers.get('content-type', '')
                if 'json' in ct or 'javascript' in ct:
                    if 'graphql' in resp.url or '/api/' in resp.url or 'threads' in resp.url:
                        harvest(resp.text())
            except Exception:
                pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                          '--disable-blink-features=AutomationControlled'],
                )
                context = browser.new_context(user_agent=_UA, locale='en-US',
                                              viewport={'width': 1280, 'height': 900})
                cookies = self._playwright_cookies()
                if cookies:
                    context.add_cookies(cookies)
                page = context.new_page()
                page.on('response', on_response)
                try:
                    page.goto(url, timeout=45000, wait_until='domcontentloaded')
                except Exception as e:
                    print(f"⚠️ goto Threads: {e}")
                # Dar tiempo a que dispare el GraphQL del post y, si hace falta,
                # forzar reproducción para que pida el media.
                page.wait_for_timeout(3000)
                if not candidates:
                    try:
                        page.mouse.click(640, 450)
                    except Exception:
                        pass
                    page.wait_for_timeout(4000)
                # Fallback: leer el src del <video> por si quedó progresivo.
                if not candidates:
                    try:
                        src = page.eval_on_selector('video', 'v => v.currentSrc || v.src')
                        if src and '.mp4' in src:
                            candidates.append((3, src))
                    except Exception:
                        pass
                title = ''
                try:
                    title = (page.title() or '').split(' on Threads')[0][:80]
                except Exception:
                    pass
                browser.close()
        except Exception as e:
            print(f"❌ Error Threads extractor: {e}")
            return {"success": False, "error": f"Error al extraer de Threads: {str(e)[:120]}"}

        if not candidates:
            return {
                "success": False,
                "error": "No se encontró video en el post de Threads (¿es solo texto/imagen o requiere login?).",
                "suggestion": "Verificá que el post tenga video y que la cookie de Meta esté cargada.",
            }

        # Mejor calidad primero (prioridad más baja = HD), deduplicado.
        candidates.sort(key=lambda c: c[0])
        seen, ordered = set(), []
        for _, u in candidates:
            base = u.split('?')[0]
            if base in seen:
                continue
            seen.add(base)
            ordered.append(u)

        return {
            "success": True,
            "data": {
                "title": title or "Threads Video",
                "uploader": "Threads",
                "duration": 0,
                "description": "Video de Threads",
                "video_formats": [{"url": ordered[0], "width": 720, "height": 1280,
                                   "format_note": "Threads"}],
            },
        }

    @staticmethod
    def _playwright_cookies():
        """Convierte el archivo Netscape combinado a cookies de Playwright para
        los dominios de Meta (threads, instagram, facebook)."""
        path = combined_cookies_file()
        if not path or not os.path.isfile(path):
            return []
        out = []
        for line in open(path, encoding='utf-8', errors='ignore'):
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) < 7:
                continue
            domain, _flag, cpath, secure, expiry, name, value = parts[:7]
            if not any(d in domain for d in ('threads', 'instagram', 'facebook')):
                continue
            cookie = {
                'name': name, 'value': value, 'domain': domain, 'path': cpath or '/',
                'secure': secure.upper() == 'TRUE', 'httpOnly': False,
            }
            if expiry.isdigit() and int(expiry) > 0:
                cookie['expires'] = int(expiry)
            out.append(cookie)
        return out
