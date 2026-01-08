#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import re
import time
from urllib.parse import urlparse


class TikTokExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae información de videos de TikTok usando yt-dlp para mejor calidad y metadata.
        """
        try:
            print(f"🔍 Extrayendo video de TikTok con yt-dlp: {url}")
            import yt_dlp

            # Configurar yt-dlp
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'timeout': 10,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                video_url = None
                if 'url' in info:
                    video_url = info['url']
                elif 'video_url' in info:
                    video_url = info['video_url']

                if video_url:
                    print(f"✅ Video TikTok extraído: {video_url[:50]}...")
                    # Get best thumbnail from list if implied 'thumbnail' is missing
                    thumbnail = info.get('thumbnail')
                    if not thumbnail and 'thumbnails' in info:
                         # Get last one (usually best quality)
                         try: thumbnail = info['thumbnails'][-1]['url']
                         except: pass

                    return {
                        "success": True,
                        "data": {
                            "videoUrl": video_url,
                            "title": info.get('title', 'Video de TikTok'),
                            "uploader": info.get('uploader', 'TikTok User'),
                            "duration": info.get('duration'),
                            "thumbnail": thumbnail,
                            "description": info.get('description', ''),
                            "view_count": info.get('view_count', 0),
                            "like_count": info.get('like_count', 0),
                            "original_url": url
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "No se encontraron enlaces de video en yt-dlp"
                    }

        except Exception as e:
            print(f"❌ Error TikTok extractor (yt-dlp): {str(e)}")
            # Fallback a lógica original podría ir aquí, pero yt-dlp es muy robusto para TikTok
            return {
                "success": False,
                "error": f"Error al extraer video de TikTok: {str(e)}",
                "suggestion": "Verifica que el video sea público"
            }

    def _extract_with_ssstik(self, url):
        # Deprecated: Kept as placeholder or removed.
        pass

    def _extract_session_data(self, html):
        pass

    def _parse_video_info(self, html, original_url):
        pass


# Test del extractor
if __name__ == "__main__":
    import sys
    # Asegurar que la consola soporte UTF-8 en Windows para emojis
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    extractor = TikTokExtractor()

    # URL de test
    test_url = "https://www.tiktok.com/@tech.tipsbyia/video/7577516435753553173?is_from_webapp=1&sender_device=pc"

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
