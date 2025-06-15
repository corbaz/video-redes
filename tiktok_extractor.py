#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import re
import time
from urllib.parse import urlparse


class TikTokExtractor:
    def __init__(self):
        self.name = "TikTok Extractor"
        self.supported_domains = ['tiktok.com', 'vm.tiktok.com']

    def extract_info(self, url):
        """
        Extrae información de videos de TikTok usando ssstik.io únicamente
        """
        try:
            return self._extract_with_ssstik(url)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al extraer video de TikTok: {str(e)}",
                "suggestion": "Verifica que el enlace sea válido y el video esté público"
            }

    def _extract_with_ssstik(self, url):
        """
        Extrae video usando ssstik.io
        """
        # Preparar headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Paso 1: Obtener la página de ssstik.io
        try:
            response = requests.get(
                'https://ssstik.io/es', headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": "No se pudo conectar con el servicio de descarga",
                "suggestion": "Verifica tu conexión a internet"
            }

        # Paso 2: Extraer token/session data si es necesario
        session_data = self._extract_session_data(response.text)

        # Paso 3: Enviar request para procesar el video
        download_data = {
            'id': url,
            'locale': 'es',
            'tt': session_data.get('tt', '')
        }

        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Referer'] = 'https://ssstik.io/es'
        headers['Origin'] = 'https://ssstik.io'

        try:
            response = requests.post(
                'https://ssstik.io/abc',
                data=download_data,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": "Error al procesar el video",
                "suggestion": "El video podría estar privado o eliminado"
            }

        # Paso 4: Extraer información del video del HTML respuesta
        return self._parse_video_info(response.text, url)

    def _extract_session_data(self, html):
        """
        Extrae datos de sesión necesarios del HTML
        """
        session_data = {}

        # Buscar token tt en el HTML
        tt_match = re.search(r'name="tt"\s+value="([^"]*)"', html)
        if tt_match:
            session_data['tt'] = tt_match.group(1)

        return session_data

    def _parse_video_info(self, html, original_url):
        """
        Extrae la información del video del HTML de respuesta
        """
        try:
            # Buscar enlaces de descarga en el HTML
            download_links = re.findall(
                r'href="([^"]*)" class="[^"]*download[^"]*"', html)

            if not download_links:
                # Buscar patrones alternativos
                download_links = re.findall(
                    r'<a[^>]*href="([^"]*)"[^>]*>.*?[Dd]ownload.*?</a>', html, re.DOTALL)

            if not download_links:
                return {
                    "success": False,
                    "error": "No se encontró enlace de descarga",
                    "suggestion": "El video podría estar protegido o eliminado"
                }

            # Usar el primer enlace válido
            video_url = download_links[0]

            # Si el enlace es relativo, hacerlo absoluto
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            elif video_url.startswith('/'):
                video_url = 'https://ssstik.io' + video_url

            # Extraer título si está disponible
            title_match = re.search(r'<title[^>]*>([^<]*)</title>', html)
            title = title_match.group(1) if title_match else "Video de TikTok"

            # Limpiar título
            title = re.sub(r'\s*-\s*ssstik\.io.*$', '', title)
            title = title.strip() or "Video de TikTok"

            # Extraer usuario del URL original
            user_match = re.search(r'@([^/]+)', original_url)
            uploader = f"@{user_match.group(1)}" if user_match else "Usuario de TikTok"

            return {
                "success": True,
                "title": title,
                "description": f"Video descargado desde TikTok via ssstik.io",
                "duration": 0,  # ssstik.io no proporciona duración
                "uploader": uploader,
                "thumbnail": "",  # ssstik.io no proporciona thumbnail en este método
                "view_count": 0,  # ssstik.io no proporciona vistas
                "video_url": video_url,
                "video_quality": "TikTok HD",
                "platform": "TikTok",
                "formats": [{"url": video_url, "quality": "HD"}]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error al procesar respuesta: {str(e)}",
                "suggestion": "Intenta con otro video de TikTok"
            }


# Test del extractor
if __name__ == "__main__":
    extractor = TikTokExtractor()

    # URL de test
    test_url = "https://www.tiktok.com/@eli.cocinaa/video/7436436767374413112"

    print(f"🎵 Probando extractor de TikTok con ssstik.io")
    print(f"📱 URL: {test_url}")
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
