import subprocess
import json
from typing import Dict, Any


class InstagramExtractor:
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
                cmd = [
                    'yt-dlp',
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

            # 2. Si falla y es una historia o error de usuario, intentar con cookies del navegador
            needs_cookies = result.returncode != 0 and (
                'stories' in url or 
                'unable to extract user info' in result.stderr or
                'private' in result.stderr.lower()
            )

            if needs_cookies:
                print("⚠️ Contenido privado/historia detectado. Intentando con cookies de Chrome...")
                # Note: If Chrome is open, this might fail with Permission Error on Windows.
                # User should ideally close the browser or run as admin, but we can't force that.
                # We can try to copy the cookie file to a temp location if possible, but yt-dlp handles this internally usually.
                # The error reported is "Could not copy Chrome cookie database".
                # This often means the browser has the file locked.
                
                # Try Chrome first
                result = run_ytdlp(['--cookies-from-browser', 'chrome'])
                
                if result.returncode != 0:
                     # Check if it was a permission error
                     if "Permission denied" in result.stderr or "Could not copy" in result.stderr:
                         print("⚠️ Error de permisos con cookies de Chrome (¿Navegador abierto?). Intentando Edge...")
                     else:
                         print("⚠️ Chrome falló. Intentando con cookies de Edge...")
                         
                     result = run_ytdlp(['--cookies-from-browser', 'edge'])

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if 'private' in error_msg.lower():
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
