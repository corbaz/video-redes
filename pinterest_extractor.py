
import json
import logging
import re
import requests
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

class PinterestExtractor:
    def __init__(self):
        self.name = "Pinterest Extractor"
        self.supported_domains = ['pinterest.com', 'pin.it']
        logger.info("PinterestExtractor v2.1 (Manual Fallback Enabled) Initialized")

    def extract_info(self, url):
        """
        Extrae información de video/imagen de Pinterest usando yt-dlp y fallback manual
        """
        try:
            # 1. Intentar primero con yt-dlp
            # yt-dlp es muy bueno para videos, pero a veces falla con imágenes o cambios de layout
            return self._extract_with_ytdlp(url)
        except Exception as e:
            logger.warning(f"yt-dlp falló para Pinterest, intentando fallback manual... Error: {e}")
            return self._extract_manual_fallback(url)

    def _extract_with_ytdlp(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'dump_single_json': True,
            'extract_flat': False,
            'ignoreerrors': True, # Importante para evitar crash total si falla algo interno
        }

        with YoutubeDL(ydl_opts) as ydl:
            # Si yt-dlp no encuentra video, suele lanzar excepción DownloadError
            info = ydl.extract_info(url, download=False)
        
        if not info:
            raise Exception("No info returned form yt-dlp")

        # Procesar info de yt-dlp
        title = info.get('title', 'Pinterest Pin')
        thumbnail = info.get('thumbnail', '')
        uploader = info.get('uploader', 'Pinterest User')
        video_url = info.get('url')

        # Buscar mejor video si no está directo
        if not video_url:
            formats = info.get('formats', [])
            best_format = None
            
            # Ordenar formatos por calidad si es posible, o buscar mp4
            # Preferir mp4, luego m3u8
            mp4_formats = [f for f in formats if f.get('ext') == 'mp4']
            m3u8_formats = [f for f in formats if f.get('ext') == 'm3u8' or f.get('protocol') == 'm3u8_native']
            
            if mp4_formats:
                # Intentar tomar el de mejor calidad (tbr o height)
                # Ordenar por height descendente, luego tbr descendente
                best_format = sorted(mp4_formats, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)[0]
            elif m3u8_formats:
                # Si solo hay m3u8 (común en transmisiones), tomar el mejor
                best_format = sorted(m3u8_formats, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)[0]
            elif formats:
                 best_format = formats[-1]
                 
            if best_format:
                video_url = best_format.get('url')

        if not video_url:
             # Si yt-dlp devuelve info pero sin video URL (quizás es imagen o playlist)
             # Permitir fallback manual si yt-dlp falla en encontrar URL de video
             raise Exception("yt-dlp found info but no video URL")

        return {
            "success": True,
            "title": title,
            "video_url": video_url,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "platform": "pinterest",
            "duration": info.get('duration', 0),
            "type": "video"
        }

    def _extract_manual_fallback(self, url):
        """
        Fallback robusto usando Regex directo sobre el HTML
        """
        try:
            logger.info(f"🕵️‍♂️ Ejecutando extracción manual (Regex) para: {url}")
            
            # Use Mobile UA to often bypass login walls and get clearer mobile structure
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.google.com/'
            }
            
            session = requests.Session()
            response = session.get(url, headers=headers, allow_redirects=True, timeout=15)
            html = response.text
            final_url = response.url 
            logger.info(f"Status Code: {response.status_code}, Length: {len(html)}")

            # Título
            og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if not og_title:
                og_title = re.search(r'<title>([^<]+)</title>', html)
            title = og_title.group(1).replace("Pinterest", "").strip() if og_title else "Pinterest Pin"
            if not title: title = "Pinterest Media"

            # 0. Check for Login Wall redirection
            if "login/" in final_url or "Log in" in html[:1000]:
                 logger.warning("Pinterest redirected to Login page. Try checking cookies or IP.")

            # 1. Buscar LD+JSON (Structured Data) - Very reliable for videos
            ld_json_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            for block in ld_json_blocks:
                try:
                    data = json.loads(block)
                    if data.get('@type') == 'VideoObject' and 'contentUrl' in data:
                        video_url = data['contentUrl']
                        thumbnail = data.get('thumbnail', {}).get('contentUrl', '') if isinstance(data.get('thumbnail'), dict) else data.get('thumbnailUrl', '')
                        logger.info(f"LD+JSON Video Found: {video_url}")
                        return {
                            "success": True,
                            "title": title,
                            "video_url": video_url,
                            "thumbnail": thumbnail,
                            "uploader": "Pinterest User",
                            "platform": "pinterest",
                            "type": "video"
                        }
                except: pass

            # 2. Buscar VIDEO (mp4) - Regex (Mejorado)
            # Buscar cualquier MP4 en el HTML, priorizando los de pinimg
            mp4_matches = re.findall(r'(https?://[^"\'\s<>]+?\.mp4)', html)
            
            if mp4_matches:
                # Filtrar coincidencias no deseadas si es necesario, pero generalmente queremos cualquier mp4
                # Priorizar los que parecen ser el contenido principal (v.pinimg.com)
                video_url = mp4_matches[0]
                for match in mp4_matches:
                    if 'v.pinimg.com' in match or 'v1.pinimg.com' in match:
                        video_url = match
                        break
                
                logger.info(f"Manual Video Found: {video_url}")
                og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                thumbnail = og_image.group(1) if og_image else ""
                
                return {
                    "success": True,
                    "title": title,
                    "video_url": video_url,
                    "thumbnail": thumbnail,
                    "uploader": "Pinterest User",
                    "platform": "pinterest",
                    "type": "video"
                }

            # 3. Buscar HLS (m3u8)
            m3u8_matches = re.findall(r'(https?://(?:v|v\d+)\.pinimg\.com/[^"\'\s<>]+?\.m3u8)', html)
            if m3u8_matches:
                 video_url = m3u8_matches[0]
                 logger.info(f"Manual HLS Found: {video_url}")
                 og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                 thumbnail = og_image.group(1) if og_image else ""
                 return {
                    "success": True,
                    "title": title,
                    "video_url": video_url,
                    "thumbnail": thumbnail,
                    "uploader": "Pinterest User",
                    "platform": "pinterest",
                    "type": "video"
                }

            # 4. Fallback genérico <video src="..."> (Lo que encontró el debug script)
            generic_video = re.search(r'<video[^>]*src="([^"]+)"', html)
            if generic_video:
                 video_url = generic_video.group(1)
                 if not video_url.startswith('http'):
                     if video_url.startswith('//'): video_url = 'https:' + video_url
                     else: video_url = 'https://pinterest.com' + video_url # Asumir relativo
                
                 logger.info(f"Generic Video Tag Found: {video_url}")
                 og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                 thumbnail = og_image.group(1) if og_image else ""
                 return {
                    "success": True,
                    "title": title,
                    "video_url": video_url,
                    "thumbnail": thumbnail,
                    "uploader": "Pinterest User",
                    "platform": "pinterest",
                    "type": "video"
                }
            
            # 2. Buscar en PWS_DATA (JSON profundo) - Attempt to find video in JSON too
            json_match = re.search(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            pws_images = []
            pws_video = None
            if json_match:
                try:
                    def recursive_find(data, found_imgs):
                        nonlocal pws_video
                        if isinstance(data, dict):
                            # Check for video in JSON
                            if 'video_list' in data and data['video_list']:
                                 # Prioritize .mp4 or .m3u8
                                 vlist = data['video_list']
                                 if 'V_720P' in vlist: pws_video = vlist['V_720P'].get('url')
                                 elif 'V_EXP7' in vlist: pws_video = vlist['V_EXP7'].get('url')
                                 elif isinstance(vlist, dict) and len(vlist) > 0:
                                      first_key = list(vlist.keys())[0]
                                      pws_video = vlist[first_key].get('url')

                            for k, v in data.items():
                                if k == 'images' and isinstance(v, dict):
                                    if 'orig' in v: found_imgs.append(v['orig']['url'])
                                    elif '736x' in v: found_imgs.append(v['736x']['url'])
                                if k == 'url' and isinstance(v, str) and 'i.pinimg.com' in v:
                                    found_imgs.append(v)
                                recursive_find(v, found_imgs)
                        elif isinstance(data, list):
                            for item in data: recursive_find(item, found_imgs)
                    
                    data = json.loads(json_match.group(1))
                    recursive_find(data, pws_images)

                    if pws_video:
                         logger.info(f"PWS_DATA Video Found: {pws_video}")
                         og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                         thumbnail = og_image.group(1) if og_image else ""
                         return {
                            "success": True,
                            "title": title,
                            "video_url": pws_video,
                            "thumbnail": thumbnail,
                            "uploader": "Pinterest User",
                            "platform": "pinterest",
                            "type": "video"
                        }

                except Exception as e:
                    logger.warning(f"Error parsing PWS_DATA: {e}")

            if pws_images:
                # Prefer originals
                best_img = pws_images[0]
                for img in pws_images:
                    if 'originals' in img:
                        best_img = img
                        break
                    elif '736x' in img:
                        best_img = img
                
                logger.info(f"PWS_DATA Image Found: {best_img}")
                return {
                    "success": True,
                    "title": title,
                    "video_url": best_img,
                    "thumbnail": best_img,
                    "uploader": "Pinterest User",
                    "platform": "pinterest",
                    "type": "image"
                }

            # 3. Buscar IMAGEN (Regex)
            # Regex más permisivo (basado en debug exitoso)
            # Primero buscamos originales
            img_matches = re.findall(r'(https?://i\.pinimg\.com/originals/[^"\'\s]+\.(?:jpg|png|jpeg|webp))', html, re.IGNORECASE)
            
            # Si no, buscamos cualquier imagen de pinimg
            if not img_matches:
                 img_matches = re.findall(r'(https?://i\.pinimg\.com/[^"\'\s]+\.(?:jpg|png|jpeg|webp))', html, re.IGNORECASE)
            
            # Filtrar íconos o avatares de 75x75 si es posible, quedándonos con los más grandes
            # (Por ahora tomamos el primero que no sea miniatura obvia si hay lista)
            
            if img_matches:
                image_url = img_matches[0]
                # Intentar encontrar uno mejor si el primero es pequeño (ej: 75x75)
                for img in img_matches:
                    if 'originals' in img or '736x' in img:
                        image_url = img
                        break

                logger.info(f"Manual Image Found: {image_url}")
                
                return {
                    "success": True,
                    "title": title,
                    "video_url": image_url, # Usar imagen como video_url para descarga
                    "thumbnail": image_url,
                    "uploader": "Pinterest User",
                    "platform": "pinterest",
                    "type": "image"
                }

            logger.error(f"No match. HTML snippet: {html[:500]}")
            return {
                "success": False,
                "error": "No se encontraron videos ni imágenes extraíbles en este Pin."
            }

        except Exception as e:
            logger.error(f"Excepción en manual fallback: {e}")
            return {
                "success": False,
                "error": f"Error manual Pinterest: {str(e)}"
            }
