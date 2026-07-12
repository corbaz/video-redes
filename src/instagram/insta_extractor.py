import os
import re
import subprocess
import json
from typing import Dict, Any, Optional

import requests

from common.ytdlp_cmd import YTDLP_CMD
from common.cookies_util import combined_cookies_file

# Optional Netscape-format cookies file (export with a browser extension while
# logged into Instagram). Checked before browser cookies since it works even
# when the browser is open and locking its cookie database.
COOKIES_FILE = os.environ.get(
    'INSTAGRAM_COOKIES_FILE',
    os.path.join(os.path.dirname(__file__), '..', '..', 'cookies', 'instagram.txt')
)


class InstagramExtractor:
    def _extract_via_embed_proxy(self, url: str) -> Optional[str]:
        """Anonymous fallback via kkinstagram (InstaFix-style embed proxy).

        With a bot User-Agent, /reel/{shortcode} responds with a 302 redirect
        to the video file on Instagram's own CDN. Returns the CDN URL, or
        None if the proxy could not resolve the video (it may respond with
        a jpeg thumbnail instead).
        """
        match = re.search(r'(?:reel|reels|p)/([A-Za-z0-9_-]+)', url)
        if not match:
            return None
        shortcode = match.group(1)
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)'
        }
        try:
            r = requests.get(
                f'https://kkinstagram.com/reel/{shortcode}/',
                headers=headers, timeout=30, allow_redirects=True, stream=True
            )
            content_type = r.headers.get('Content-Type', '')
            final_url = r.url
            r.close()
            if 'video' in content_type and 'cdninstagram.com' in final_url:
                return final_url
        except requests.RequestException as e:
            print(f"⚠️ Fallback embed proxy falló: {e}")
        return None

    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae video de Instagram usando yt-dlp.
        """
        try:
            print(f"🔍 Extrayendo video de Instagram: {url}")
            
            # 0. Soporte directo para URLs de CDN (scontent-*.cdninstagram.com)
            if 'cdninstagram.com' in url or '.mp4' in url:
                print("✅ URL directa de CDN detectada. Omitiendo extracción yt-dlp.")
                return {
                    "success": True,
                    "data": {
                        "title": "Instagram Story/Video (CDN Direct)",
                        "uploader": "Instagram User",
                        "duration": 0,
                        "description": "Video directo de Instagram",
                        "video_formats": [{
                            "url": url,
                            "width": 720,
                            "height": 1280,
                            "format_note": "CDN Source"
                        }]
                    }
                }

            def run_ytdlp(extra_args=None):
                cmd = YTDLP_CMD + [
                    '--dump-json',
                    '--no-download',
                    '--format', 'best[ext=mp4]/best',
                    url
                ]
                if extra_args:
                    cmd.extend(extra_args)
                
                return subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60)

            # 1. Intentar método estándar
            result = run_ytdlp()

            # 2. Si falla por contenido que requiere autenticación, reintentar con cookies.
            # Instagram devuelve "empty media response" cuando exige login (comportamiento
            # desde 2026 para la mayoría de los reels).
            stderr_lower = result.stderr.lower()
            needs_cookies = result.returncode != 0 and (
                'stories' in url or
                'unable to extract user info' in stderr_lower or
                'private' in stderr_lower or
                'empty media response' in stderr_lower or
                'login required' in stderr_lower or
                'rate-limit' in stderr_lower or
                'use --cookies' in stderr_lower
            )

            if needs_cookies:
                print("⚠️ Instagram requiere autenticación. Reintentando con cookies...")

                # 2a. Archivo de cookies exportado. Combina todos los .txt de
                # la carpeta cookies/ (soporta los per-dominio de la extensión).
                cookies_path = combined_cookies_file()
                if cookies_path:
                    print(f"🍪 Usando archivo de cookies: {cookies_path}")
                    result = run_ytdlp(['--cookies', cookies_path])

            # 3. Fallback anónimo rápido: proxy de embeds (kkinstagram).
            # Va antes que las cookies del navegador porque estas suelen fallar
            # con el navegador abierto (base de cookies bloqueada en Windows).
            if result.returncode != 0:
                print("🔁 Intentando fallback vía proxy de embeds...")
                cdn_url = self._extract_via_embed_proxy(url)
                if cdn_url:
                    print("✅ Video obtenido vía proxy de embeds (CDN directo).")
                    return {
                        "success": True,
                        "data": {
                            "title": "Instagram Reel",
                            "uploader": "Instagram User",
                            "duration": 0,
                            "description": "Video obtenido vía proxy de embeds",
                            "video_formats": [{
                                "url": cdn_url,
                                "width": 720,
                                "height": 1280,
                                "format_note": "CDN (embed proxy)"
                            }]
                        }
                    }

            # 4. Último recurso: cookies del navegador. Nota: en Windows el
            # navegador abierto bloquea su base de cookies ("Could not copy
            # ... cookie database").
            if result.returncode != 0 and needs_cookies:
                for browser in ('chrome', 'edge', 'firefox'):
                    if result.returncode == 0:
                        break
                    print(f"🍪 Intentando con cookies de {browser}...")
                    result = run_ytdlp(['--cookies-from-browser', browser])

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if needs_cookies:
                    # El contenido requiere login y ningún método de cookies funcionó.
                    return {
                        "success": False,
                        "needs_login": True,
                        "login_platform": "instagram",
                        "error": "Instagram exige iniciar sesión para ver este contenido y no se pudieron obtener cookies válidas del navegador.",
                        "suggestion": "Inicia sesión para este video, o exporta tus cookies de Instagram a 'cookies/instagram.txt' (formato Netscape) con una extensión como 'Get cookies.txt LOCALLY'."
                    }
                if 'empty media response' in error_msg.lower():
                    return {
                        "success": False,
                        "needs_login": True,
                        "login_platform": "instagram",
                        "error": "Instagram exige iniciar sesión para ver este contenido y no se pudieron obtener cookies válidas.",
                        "suggestion": "Inicia sesión para este video, o exporta tus cookies de Instagram a 'cookies/instagram.txt' (formato Netscape) con una extensión como 'Get cookies.txt LOCALLY'."
                    }
                elif 'private' in error_msg.lower():
                    return {
                        "success": False,
                        "error": "Este contenido es privado o requiere autenticación",
                        "suggestion": "Intenta con videos públicos de cuentas verificadas"
                    }
                elif 'not available' in error_msg.lower():
                    return {
                        "success": False,
                        "error": "El video no está disponible o fue eliminado",
                        "suggestion": "Verifica que el enlace sea correcto y el video esté público"
                    }
                elif "could not copy" in error_msg.lower() or "permission denied" in error_msg.lower():
                    return {
                        "success": False,
                        "error": "El navegador bloqueó el acceso a las cookies.",
                        "suggestion": "⚠️ CIERRA COMPLETAMENTE CHROME/EDGE y vuelve a intentarlo. El navegador tiene bloqueado el archivo de sesión."
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error al acceder al video: {error_msg[:100]}...",
                        "suggestion": "Intenta con otro video o verifica tu conexión"
                    }

            # Parsear la respuesta JSON
            video_info = json.loads(result.stdout)

            # Procesar formatos para obtener solo MP4 con audio
            formats = video_info.get('formats', [])
            video_formats = []

            for fmt in formats:
                if (fmt.get('ext') == 'mp4' and
                    fmt.get('acodec') != 'none' and
                        fmt.get('vcodec') != 'none'):
                    video_formats.append({
                        "url": fmt.get('url'),
                        "width": fmt.get('width'),
                        "height": fmt.get('height'),
                        "filesize": fmt.get('filesize'),
                        "vcodec": fmt.get('vcodec'),
                        "acodec": fmt.get('acodec'),
                        "abr": fmt.get('abr'),
                        "audio_channels": fmt.get('audio_channels', 2),
                        "fps": fmt.get('fps'),
                        "format_note": fmt.get('format_note', 'MP4')
                    })

            if not video_formats:
                return {
                    "success": False,
                    "error": "No se encontraron formatos MP4 con audio",
                    "suggestion": "Este video puede no tener audio o estar en formato no compatible"
                }

            # Preparar datos de respuesta
            data = {
                "title": video_info.get('title', 'Video de Instagram'),
                "uploader": video_info.get('uploader', ''),
                "uploader_id": video_info.get('uploader_id', ''),
                "uploader_url": video_info.get('uploader_url', ''),
                "upload_date": video_info.get('upload_date', ''),
                "duration": video_info.get('duration'),
                "like_count": video_info.get('like_count'),
                "comment_count": video_info.get('comment_count'),
                "view_count": video_info.get('view_count'),
                "description": video_info.get('description', ''),
                "tags": video_info.get('tags', []),
                "video_formats": video_formats
            }

            print(
                f"✅ Video extraído: {len(video_formats)} formatos encontrados")
            return {"success": True, "data": data}

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tiempo de espera agotado",
                "suggestion": "El video puede ser muy grande o la conexión es lenta"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Error al procesar la respuesta del servidor",
                "suggestion": "Intenta nuevamente en unos momentos"
            }
        except Exception as e:
            print(f"❌ Error Instagram extractor: {str(e)}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)[:100]}...",
                "suggestion": "Verifica que yt-dlp esté instalado correctamente"
            }
