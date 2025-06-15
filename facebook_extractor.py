#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import sys
import os


class FacebookExtractor:
    def __init__(self):
        self.name = "Facebook Extractor"
        self.supported_domains = ['facebook.com', 'fb.watch', 'm.facebook.com']

    def extract_info(self, url):
        """
        Extrae información de videos de Facebook usando yt-dlp
        """
        try:
            return self._extract_with_ytdlp(url)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al extraer video de Facebook: {str(e)}",
                "suggestion": "Verifica que el enlace sea válido y el video esté público"
            }

    def _extract_with_ytdlp(self, url):
        """
        Extrae video usando yt-dlp
        """
        try:
            # Comando yt-dlp optimizado para Facebook
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '--no-playlist',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--add-header', 'Referer:https://www.facebook.com/',
                url
            ]

            # Ejecutar yt-dlp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )

            if result.returncode != 0:
                error_msg = result.stderr.lower()

                # Detectar tipos específicos de errores
                if 'private' in error_msg or 'unavailable' in error_msg:
                    return {
                        "success": False,
                        "error": "Este video es privado o no está disponible",
                        "suggestion": "Intenta con videos públicos de Facebook"
                    }
                elif 'not available' in error_msg or 'video data' in error_msg:
                    return {
                        "success": False,
                        "error": "El video no está disponible o fue eliminado",
                        "suggestion": "Verifica que el enlace sea correcto"
                    }
                elif 'sign in' in error_msg or 'login' in error_msg:
                    return {
                        "success": False,
                        "error": "Este video requiere estar conectado en Facebook",
                        "suggestion": "Intenta con videos públicos que no requieran login"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error: {error_msg[:150]}",
                        "suggestion": "Intenta con otro video de Facebook"
                    }

            # Parsear la respuesta JSON
            video_info = json.loads(result.stdout)

            # Procesar formatos para obtener el mejor MP4
            formats = video_info.get('formats', [])
            best_format = None

            # Buscar formato MP4 con audio y video
            for fmt in formats:
                if (fmt.get('ext') == 'mp4' and
                    fmt.get('acodec') != 'none' and
                        fmt.get('vcodec') != 'none'):
                    best_format = fmt
                    break

            # Si no hay formato completo, buscar cualquier MP4
            if not best_format:
                for fmt in formats:
                    if fmt.get('ext') == 'mp4':
                        best_format = fmt
                        break

            if not best_format:
                return {
                    "success": False,
                    "error": "No se encontraron formatos de video compatibles",
                    "suggestion": "Este video podría usar un formato no soportado"
                }

            # Extraer metadatos
            title = video_info.get('title', 'Video de Facebook')
            description = video_info.get('description', '')
            duration = video_info.get('duration', 0)
            uploader = video_info.get('uploader', 'Usuario de Facebook')
            thumbnail = video_info.get('thumbnail', '')
            view_count = video_info.get('view_count', 0)

            return {
                "success": True,
                "title": title,
                "description": description,
                "duration": duration,
                "uploader": uploader,
                "thumbnail": thumbnail,
                "view_count": view_count,
                "video_url": best_format["url"],
                "video_quality": f"{best_format.get('width', 'N/A')}x{best_format.get('height', 'N/A')}",
                "platform": "Facebook",
                "formats": [best_format]
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tiempo de espera agotado al procesar el video",
                "suggestion": "Intenta nuevamente o verifica tu conexión a internet"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Error al procesar la respuesta del servidor",
                "suggestion": "El video podría tener un formato no compatible"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "suggestion": "Intenta con otro enlace de Facebook"
            }


# Test del extractor
if __name__ == "__main__":
    extractor = FacebookExtractor()

    # URL de test
    test_url = "https://www.facebook.com/share/r/1CSJrste8f/"

    print(f"📘 Probando extractor de Facebook")
    print(f"🔗 URL: {test_url}")
    print(f"⏳ Extrayendo...")

    result = extractor.extract_info(test_url)

    if result["success"]:
        print(f"✅ ¡Éxito!")
        print(f"📺 Título: {result['title']}")
        print(f"👤 Usuario: {result['uploader']}")
        print(f"🎥 Calidad: {result['video_quality']}")
        print(f"🔗 URL del video: {result['video_url']}")
        print(f"🚀 Plataforma: {result['platform']}")
    else:
        print(f"❌ Error: {result['error']}")
        print(f"💡 Sugerencia: {result['suggestion']}")
