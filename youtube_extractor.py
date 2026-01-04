#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import sys
import os


class YouTubeExtractor:
    def __init__(self):
        self.name = "YouTube Extractor"
        self.supported_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']

    def extract_info(self, url):
        """
        Extrae información de videos y shorts de YouTube usando yt-dlp
        """
        try:
            return self._extract_with_ytdlp(url)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al extraer video de YouTube: {str(e)}",
                "suggestion": "Verifica que el enlace sea válido y el video esté público"
            }

    def _extract_with_ytdlp(self, url):
        """
        Extrae video usando yt-dlp con selección automática de mejor calidad
        """
        # Lista de formatos a probar en orden de preferencia
        formats_to_try = [
            # 1. Progressive MP4 (Audio+Video) - HTTP/HTTPS direct link only
            'best[ext=mp4][protocol^=http]',
            # 2. Fallback: any MP4 with http protocol
            'best[ext=mp4][protocol^=http]/best[protocol^=http]'
        ]

        for i, format_selector in enumerate(formats_to_try):
            try:
                print(
                    f"🎥 Intento {i+1}: Probando formato '{format_selector}' para {url}")

                cmd = [
                    'yt-dlp',
                    '--dump-json',
                    '--no-warnings',
                    '--no-playlist',
                    '--format', format_selector,
                    url
                ]

                # Ejecutar yt-dlp
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=45,
                    encoding='utf-8'
                )

                print(f"📊 Return code: {result.returncode}")

                if result.returncode == 0:
                    print(f"✅ Formato exitoso: {format_selector}")
                    break
                else:
                    error_msg = result.stderr
                    print(f"❌ Fallo formato {i+1}: {error_msg}")
                    if i == len(formats_to_try) - 1:
                        # Si es el último intento y falló, usar extracción básica
                        return self._extract_basic_format(url)
                    continue

            except Exception as e:
                print(f"❌ Error en intento {i+1}: {str(e)}")
                if i == len(formats_to_try) - 1:
                    return self._extract_basic_format(url)
                continue

        # Si llegamos aquí, uno de los formatos funcionó
        try:
            # Parsear la respuesta JSON
            try:
                video_info = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"❌ Error JSON: {e}")
                return self._extract_basic_format(url)

            # Extraer URL del video
            video_url = video_info.get('url')
            if not video_url:
                print("❌ No se encontró URL en video_info")
                return self._extract_basic_format(url)

            # Detectar si es un Short
            is_short = self._is_youtube_short(url, video_info)

            # Extraer metadatos
            title = video_info.get('title', 'Video de YouTube')
            description = video_info.get('description', '')
            duration = video_info.get('duration', 0)
            uploader = video_info.get(
                'uploader', video_info.get('channel', 'Canal de YouTube'))
            thumbnail = video_info.get('thumbnail', '')
            view_count = video_info.get('view_count', 0)
            like_count = video_info.get('like_count', 0)

            # Información de formato mejorada
            format_info = video_info.get('format', 'YouTube MP4')
            width = video_info.get('width', 'N/A')
            height = video_info.get('height', 'N/A')
            filesize = video_info.get('filesize', 'N/A')
            filesize_approx = video_info.get('filesize_approx', 'N/A')
            tbr = video_info.get('tbr', 'N/A')
            vbr = video_info.get('vbr', 'N/A')
            abr = video_info.get('abr', 'N/A')

            # Formatear tamaño de archivo
            if filesize != 'N/A' and filesize:
                filesize_mb = round(filesize / (1024 * 1024), 1)
                filesize_str = f"{filesize_mb} MB"
            elif filesize_approx != 'N/A' and filesize_approx:
                filesize_mb = round(filesize_approx / (1024 * 1024), 1)
                filesize_str = f"~{filesize_mb} MB"
            else:
                filesize_str = "N/A"

            # Crear etiqueta de calidad
            if height != 'N/A' and height:
                quality_label = f"{height}p"
                if width != 'N/A' and width:
                    quality_label = f"{width}x{height}"
            else:
                quality_label = "Auto"

            # Verificar si tiene audio
            has_audio = abr != 'N/A' or 'audio' in format_info.lower()

            # Log de información de calidad en consola
            print(f"✅ Video extraído exitosamente (CALIDAD OPTIMIZADA):")
            print(f"   📺 Título: {title[:50]}...")
            print(f"   🎯 Resolución: {quality_label}")
            print(f"   📁 Tamaño: {filesize_str}")
            print(f"   ⏱️ Duración: {duration}s")
            print(f"   📊 Bitrate total: {tbr} kbps" if tbr != 'N/A' else "")
            print(f"   🎬 Bitrate video: {vbr} kbps" if vbr != 'N/A' else "")
            print(f"   🔊 Bitrate audio: {abr} kbps" if abr != 'N/A' else "")
            print(f"   📱 Es Short: {'Sí' if is_short else 'No'}")
            print(f"   🔊 Audio: {'Incluido' if has_audio else 'No incluido'}")
            print(f"   🎥 Formato usado: {format_selector}")

            return {
                "success": True,
                "title": title,
                "description": description,
                "duration": duration,
                "uploader": uploader,
                "thumbnail": thumbnail,
                "view_count": view_count,
                "like_count": like_count,
                "video_url": video_url,
                "video_quality": quality_label,
                "quality_label": quality_label,
                "filesize": filesize_str,
                "bitrate": f"{tbr} kbps" if tbr != 'N/A' else "N/A",
                "video_bitrate": f"{vbr} kbps" if vbr != 'N/A' else "N/A",
                "audio_bitrate": f"{abr} kbps" if abr != 'N/A' else "N/A",
                "has_audio": has_audio,
                "platform": "YouTube Short" if is_short else "YouTube",
                "is_short": is_short,
                "format_info": format_info,
                "format_used": format_selector,
                "formats": [{"url": video_url, "quality": quality_label, "filesize": filesize_str}]
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
                "suggestion": "Intenta con otro enlace de YouTube"
            }

    def _extract_basic_format(self, url):
        """
        Extrae video usando formato básico como fallback
        """
        try:
            print("🔄 Usando extracción básica como fallback...")

            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '--no-playlist',
                '--format', 'best[ext=mp4]/best',
                url
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,
                encoding='utf-8'
            )

            print(f"📊 Basic extraction return code: {result.returncode}")

            if result.returncode != 0:
                error_msg = result.stderr
                print(f"❌ Error en extracción básica: {error_msg}")
                return {
                    "success": False,
                    "error": "No se pudo extraer el video con formato básico",
                    "suggestion": "El video podría no estar disponible o tener restricciones"
                }

            try:
                video_info = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"❌ Error JSON en básico: {e}")
                return {
                    "success": False,
                    "error": "Error al procesar respuesta del video",
                    "suggestion": "El video podría tener un formato no compatible"
                }

            video_url = video_info.get('url')

            if not video_url:
                print("❌ No se encontró URL en extracción básica")
                return {
                    "success": False,
                    "error": "No se pudo obtener la URL del video",
                    "suggestion": "El video podría tener restricciones"
                }

            # Detectar si es un Short
            is_short = self._is_youtube_short(url, video_info)

            # Metadatos básicos
            title = video_info.get('title', 'Video de YouTube')
            uploader = video_info.get('uploader', 'Canal de YouTube')
            thumbnail = video_info.get('thumbnail', '')
            duration = video_info.get('duration', 0)

            # Información de calidad básica
            width = video_info.get('width', 'N/A')
            height = video_info.get('height', 'N/A')
            filesize = video_info.get('filesize', 'N/A')
            abr = video_info.get('abr', 'N/A')

            # Crear etiqueta de calidad
            if height != 'N/A' and height:
                quality_label = f"{height}p"
                if width != 'N/A' and width:
                    quality_label = f"{width}x{height}"
            else:
                quality_label = "Auto"

            # Formatear tamaño
            if filesize != 'N/A' and filesize:
                filesize_mb = round(filesize / (1024 * 1024), 1)
                filesize_str = f"{filesize_mb} MB"
            else:
                filesize_str = "N/A"

            # Verificar audio
            has_audio = abr != 'N/A'

            # Log de información básica
            print(f"✅ Extracción básica exitosa (CALIDAD ESTÁNDAR):")
            print(f"   📺 Título: {title[:50]}...")
            print(f"   🎯 Resolución: {quality_label}")
            print(f"   📁 Tamaño: {filesize_str}")
            print(f"   ⏱️ Duración: {duration}s")
            print(f"   📱 Es Short: {'Sí' if is_short else 'No'}")
            print(f"   🔊 Audio: {'Incluido' if has_audio else 'No incluido'}")

            return {
                "success": True,
                "title": title,
                "uploader": uploader,
                "thumbnail": thumbnail,
                "duration": duration,
                "video_url": video_url,
                "video_quality": quality_label,
                "quality_label": quality_label,
                "filesize": filesize_str,
                "has_audio": has_audio,
                "platform": "YouTube Short" if is_short else "YouTube",
                "is_short": is_short,
                "formats": [{"url": video_url, "quality": quality_label, "filesize": filesize_str}]
            }

        except Exception as e:
            print(f"❌ Error en extracción básica: {str(e)}")
            return {
                "success": False,
                "error": f"Error en extracción básica: {str(e)}",
                "suggestion": "Intenta con otro enlace de YouTube"
            }

    def _is_youtube_short(self, url, video_info):
        """
        Detecta si es un YouTube Short basado en URL y metadatos
        """
        # Verificar URL
        if '/shorts/' in url:
            return True

        # Verificar duración (Shorts suelen ser <= 60 segundos)
        duration = video_info.get('duration', 0)
        if duration and duration <= 60:
            return True

        # Verificar dimensiones (Shorts son verticales)
        width = video_info.get('width', 0)
        height = video_info.get('height', 0)
        if width and height and height > width:
            return True

        return False


# Función de utilidad para testing rápido
def test_extractor():
    """Función de prueba rápida"""
    extractor = YouTubeExtractor()
    print("🎥 YouTube Extractor inicializado correctamente")
    print("📊 Formatos optimizados para mejor calidad con audio")
    print("🔊 Audio incluido automáticamente cuando sea posible")
    print("✅ Listo para usar")
    return True


if __name__ == "__main__":
    test_extractor()
