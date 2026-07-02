#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import sys
import os

from common.ytdlp_cmd import YTDLP_CMD


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
        Extrae video usando yt-dlp como librería (NO subprocess) para mayor precisión
        y detección de formatos DASH.
        """
        from yt_dlp import YoutubeDL
        import logging

        # Configuración para obtener TODOS los formatos, incluyendo DASH
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'youtube_include_dash_manifest': True,
            'youtube_include_hls_manifest': True,
            'extract_flat': False,
        }

        try:
            print(f"🔍 Analizando video con YT-DLP (Full Scan) de: {url}")
            with YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(url, download=False)

            if not video_info:
                return self._extract_basic_format(url)

            # 1. Detectar máxima calidad (DASH includo)
            all_formats = video_info.get('formats', [])
            max_height = 0
            for f in all_formats:
                h = f.get('height')
                # A veces el height está en string o None, nos aseguramos
                try:
                    if h and int(h) > max_height:
                        max_height = int(h)
                except:
                    continue
            
            max_quality_msg = f"{max_height}p" if max_height > 0 else "Auto"

            # 2. Buscar video para Preview (Progresivo: Video+Audio en un archivo)
            preview_format = None
            best_preview_h = 0
            
            # Buscamos el mejor formato que tenga VIDEO Y AUDIO (Progresivo o HLS)
            # Priorizamos calidad sobre protocolo
            for f in all_formats:
                has_video = f.get('vcodec') != 'none' and f.get('vcodec') is not None
                has_audio = f.get('acodec') != 'none' and f.get('acodec') is not None
                protocol = f.get('protocol', '')
                # Algunos protocolos m3u8_native de YouTube ya traen audio y video mezclados
                is_playable = protocol.startswith('http') or 'm3u8' in protocol
                
                if has_video and has_audio and is_playable:
                    h = f.get('height', 0) or 0
                    # Si es el mismo height, preferimos http sobre m3u8 por compatibilidad nativa
                    if h > best_preview_h:
                        best_preview_h = h
                        preview_format = f
                    elif h == best_preview_h and protocol.startswith('http'):
                        preview_format = f

            # Fallback Preview: Si no hay progresivo ideal, buscamos cualquier cosa con URL
            if not preview_format:
                for f in all_formats:
                    if f.get('url') and f.get('protocol', '').startswith('http'):
                        preview_format = f
                        break
            
            if not preview_format:
                 raise Exception("No se encontró ningún formato reproducible para preview")

            video_url = preview_format.get('url')
            # Si el height es None, ponemos un label genérico
            h_val = preview_format.get('height')
            quality_label = f"{h_val}p" if h_val else "Auto"
            
            # Datos generales
            title = video_info.get('title', 'Video de YouTube')
            uploader = video_info.get('uploader') or video_info.get('channel', 'Desconocido')
            duration = video_info.get('duration', 0)
            thumbnail = video_info.get('thumbnail', '')
            
            # Formatear tamaño
            filesize = preview_format.get('filesize') or preview_format.get('filesize_approx')
            filesize_str = "N/A"
            if filesize:
                filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB"
            
            # Detectar Shorts
            is_short = self._is_youtube_short(url, video_info)

             # Log de información de calidad en consola
            print(f"✅ Extracción Exitosa:")
            print(f"   📺 Título: {title[:60]}...")
            print(f"   🔥 Calidad Máxima Detectada: {max_quality_msg} (DASH)")
            print(f"   👀 Calidad Preview: {quality_label}")
            print(f"   📂 Tamaño Preview: {filesize_str}")

            return {
                "success": True,
                "title": title,
                "description": video_info.get('description', ''),
                "duration": duration,
                "uploader": uploader,
                "thumbnail": thumbnail,
                "view_count": video_info.get('view_count', 0),
                "like_count": video_info.get('like_count', 0),
                "video_url": video_url,
                "original_url": url, 
                "video_quality": quality_label,
                "max_quality": max_quality_msg,
                "quality_label": quality_label,
                "filesize": filesize_str,
                "has_audio": True,
                "platform": "YouTube Short" if is_short else "YouTube",
                "is_short": is_short,
                "formats": []
            }

        except Exception as e:
            print(f"❌ Error yt-dlp lib: {e}")
            return self._extract_basic_format(url)



    def _extract_basic_format(self, url):
        """
        Extrae video usando formato básico como fallback
        """
        try:
            print("🔄 Usando extracción básica como fallback...")

            cmd = YTDLP_CMD + [
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
                "original_url": url,
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
