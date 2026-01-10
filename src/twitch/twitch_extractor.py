#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yt_dlp
from typing import Dict, Any

class TwitchExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae información de videos de Twitch usando yt-dlp.
        """
        try:
            print(f"🔍 Extrayendo video de Twitch con yt-dlp: {url}")
            
            # Configurar yt-dlp
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'timeout': 10,
                # Twitch specific optimization if needed
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Twitch VODs usually have 'url' pointing to the m3u8 playlist or similar
                video_url = info.get('url') or info.get('webpage_url')
                
                if video_url:
                    print(f"✅ Video Twitch extraído: {info.get('title', 'Sin título')}")
                    
                    return {
                        "success": True,
                        "data": {
                            "videoUrl": video_url,
                            "original_url": info.get('webpage_url', url), # Crucial for server.py to use yt-dlp for download
                            "title": info.get('title', 'Video de Twitch'),
                            "uploader": info.get('uploader', 'Twitch Streamer'),
                            "duration": info.get('duration'),
                            "thumbnail": info.get('thumbnail'),
                            "description": info.get('description', ''),
                            "view_count": info.get('view_count', 0),
                            "platform": "twitch"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "No se encontraron enlaces de video en Twitch"
                    }

        except Exception as e:
            print(f"❌ Error Twitch extractor: {str(e)}")
            return {
                "success": False,
                "error": f"Error al extraer video de Twitch: {str(e)}",
            }

if __name__ == "__main__":
    extractor = TwitchExtractor()
    test_url = "https://www.twitch.tv/videos/2663661756" # User provided example
    # Note: If that specific URL is invalid/old, it might fail, but code logic holds.
    # Twitch VODs expire.
    print(extractor.extract_info("https://www.twitch.tv/videos/2000000000")) # Dummy ID for structure check
