import subprocess
import json
import re
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup


class LinkedInExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae solo la URL del video y el HTML bruto de la publicación de LinkedIn.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            print(f"🔍 Extrayendo video de LinkedIn: {url}")
            resp = requests.get(url, headers=headers,
                                timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                return {"success": False, "error": f"No se pudo acceder a la URL (status {resp.status_code})"}
            html = resp.text
            # Buscar la URL del video (igual que antes)
            video_url = None
            # Buscar <video> tag
            soup = BeautifulSoup(html, "html.parser")
            video_tag = soup.find("video")
            if video_tag:
                video_url = video_tag.get("src") or video_tag.get("data-src")
                if not video_url:
                    source_tag = video_tag.find("source")
                    if source_tag:
                        video_url = source_tag.get(
                            "src") or source_tag.get("data-src")
            # Regex fallback
            if not video_url:
                video_patterns = [
                    r'"progressiveUrl":"([^"]+\.mp4[^"]*)"',
                    r'"videoUrl":"([^"]+\.mp4[^"]*)"',
                    r'"hlsVideoUrl":"([^"]+)"',
                    r'"dashVideoUrl":"([^"]+)"',
                    r'data-video-src="([^"]+)"',
                    r'"(https://[^"]*\.mp4[^"]*)"',
                    r'"(https://video\.linkedin\.com/[^"]+)"',
                    r'"(https://dms\.licdn\.com/[^"]*\.mp4[^"]*)"',
                    r'videoUrl["\"]:s*["\"]([^"\"]+)["\"]',
                    r'progressiveUrl["\"]:s*["\"]([^"\"]+)["\"]',
                    r'"videoSrc":"([^"]+)"',
                    r'mp4["\"]:s*[""]([^"\"]+)["\"]'
                ]
                for pattern in video_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        video_url = matches[0]
                        break
            # Buscar en todos los <script> embebidos (UGC y posts modernos)
            if not video_url:
                scripts = soup.find_all('script')
                for script in scripts:
                    script_content = script.string or script.text or ''
                    # Buscar URLs de video en cada script
                    for pattern in video_patterns:
                        matches = re.findall(
                            pattern, script_content, re.IGNORECASE)
                        if matches:
                            video_url = matches[0]
                            break
                    if video_url:
                        break
            # Buscar blobs y URLs modernas
            if not video_url:
                blob_patterns = [
                    r'"(blob:https://www.linkedin.com/[^"]+)"',
                    r'"(https://media.licdn.com/dms/video/[^\"]+\.mp4[^"]*)"',
                    r'"(https://media.licdn.com/dms/video/[^\"]+)"',
                ]
                for pattern in blob_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        video_url = matches[0]
                        break
            # Buscar en JSON embebido (LinkedIn suele poner info en window.__INITIAL_DATA__)
            if not video_url:
                json_data = None
                for script in scripts:
                    script_content = script.string or script.text or ''
                    if 'window.__INITIAL_DATA__' in script_content:
                        try:
                            json_text = script_content.split('window.__INITIAL_DATA__ = ')[
                                1].split(';')[0].strip()
                            json_data = json.loads(json_text)
                            # Buscar cualquier campo que contenga .mp4

                            def find_mp4(obj):
                                if isinstance(obj, dict):
                                    for v in obj.values():
                                        res = find_mp4(v)
                                        if res:
                                            return res
                                elif isinstance(obj, list):
                                    for v in obj:
                                        res = find_mp4(v)
                                        if res:
                                            return res
                                elif isinstance(obj, str) and '.mp4' in obj:
                                    return obj
                                return None
                            found = find_mp4(json_data)
                            if found:
                                video_url = found
                                break
                        except Exception:
                            continue
            if not video_url:
                return {"success": False, "error": "No se encontró video en esta publicación de LinkedIn. Puede ser privado, estar protegido, o LinkedIn ha cambiado la forma de incrustar el video. Intenta con otro post o revisa si el video es público."}
            # Limpiar URL si tiene parámetros extra
            if "?" in video_url:
                video_url = video_url.split("?")[0]
            print(f"✅ Video extraído: {video_url[:50]}...")
            return {"success": True, "video_url": video_url, "html": html}
        except Exception as e:
            print(f"❌ Error LinkedIn extractor: {str(e)}")
            return {"success": False, "error": f"Error al extraer video de LinkedIn: {str(e)}"}
