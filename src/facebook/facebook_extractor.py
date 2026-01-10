#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import sys
import os
import re


class FacebookExtractor:
    def __init__(self):
        self.name = "Facebook Extractor"
        self.supported_domains = ['facebook.com', 'fb.watch', 'm.facebook.com']

    def extract_info(self, url):
        """
        Extrae información de videos de Facebook usando yt-dlp con fallback manual y reintento por ID
        """
        try:
            # 1. Intentar primero con yt-dlp normal
            result = self._extract_with_ytdlp(url)
            if result.get('success'):
                return result
            
            # 2. Si falló yt-dlp, ver si podemos extraer un ID del error para reintentar con URL canónica
            # Revisar si _extract_with_ytdlp nos devolvió un detected_id
            if result.get('detected_id'):
                video_id = result['detected_id']
                canonical_url = f"https://www.facebook.com/reel/{video_id}"
                print(f"🔄 ID recuperado ({video_id}), reintentando fallbacks manuales con URL limpia: {canonical_url}")
                return self._extract_manual(canonical_url)

            # Si no hay ID en detected_id, intentamos buscarlo en el mensaje de error por si acaso
            error_msg = result.get('error', '')
            # print(f"DEBUG Error msg: {error_msg}")
            
            # Regex más flexible para capturar ID numérico largo asociado a facebook
            id_match = re.search(r'facebook.*?(\d{10,20})', error_msg, re.IGNORECASE)
            if not id_match:
                 # Intentar solo digitos si no hay 'facebook' cerca pero es el comienzo del error de yt-dlp
                 id_match = re.search(r'error:\s*\[.*?\]\s*(\d{10,20})', error_msg, re.IGNORECASE)

            if id_match:
                video_id = id_match.group(1)
                canonical_url = f"https://www.facebook.com/reel/{video_id}"
                print(f"🔄 ID detectado en error ({video_id}), reintentando fallbacks manuales con URL canónica: {canonical_url}")
                return self._extract_manual(canonical_url)
                if canonical_url not in url: # Evitar bucle infinito
                    print(f"🔄 ID detectado en error ({video_id}), reintentando con URL canónica: {canonical_url}")
                    # Reintentar yt-dlp con URL limpia
                    result_retry = self._extract_with_ytdlp(canonical_url)
                    if result_retry.get('success'):
                        return result_retry
                    
                    # Si falla yt-dlp, intentar manual con esta URL limpia
                    print(f"⚠️ Reintento yt-dlp falló, probando manual con: {canonical_url}")
                    return self._extract_manual(canonical_url)

            print(f"⚠️ yt-dlp falló, intentando extracción manual para: {url}")
            return self._extract_manual(url)
            
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
            # Intentar resolver redirección si es una URL corta de share
            final_url = url
            if '/share/' in url:
                try:
                    import requests
                    # Usar HEAD para seguir redirecciones sin bajar el cuerpo
                    response = requests.head(url, allow_redirects=True, timeout=5, headers={
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    })
                    if response.url != url:
                        print(f"🔄 Redirección resuelta: {url} -> {response.url}")
                        final_url = response.url
                except Exception as e:
                    print(f"⚠️ No se pudo resolver redirección: {e}")

            # Comando yt-dlp optimizado para Facebook
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '--no-playlist',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--add-header', 'Referer:https://www.facebook.com/',
                final_url
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
                # Primero: ¿Podemos recuperar el ID del error para intentar URL directa de Reel?
                # Ej: [facebook] 1787905208566913: cannot parse data
                id_match_err = re.search(r'facebook.*?(\d{10,20})', error_msg)
                if id_match_err:
                     video_id = id_match_err.group(1)
                     print(f"⚠️ Detectado ID {video_id} en error, intentando URL directa de Reel...")
                     reel_url = f"https://www.facebook.com/reel/{video_id}"
                     if reel_url not in final_url:
                         cmd[-1] = reel_url
                         result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
                         if result.returncode == 0:
                             # Si funcionó, genial
                             pass
                         else:
                             # Si falló, actualizar error pero mantener rastro
                             error_msg = result.stderr.lower()

                # Si sigue fallando y es "cannot parse data", intentar modo móvil
                if result.returncode != 0 and 'cannot parse data' in error_msg and 'm.facebook.com' not in final_url:
                     # Intentar con versión móvil si falló la versión de escritorio
                     print("⚠️ Fallo con www.facebook.com, intentando con m.facebook.com...")
                     mobile_url = final_url.replace('www.facebook.com', 'm.facebook.com').replace('web.facebook.com', 'm.facebook.com')
                     if 'm.facebook.com' not in mobile_url:
                         mobile_url = mobile_url.replace('facebook.com', 'm.facebook.com')
                     
                     cmd[-1] = mobile_url
                     # Reintentar
                     result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
                     if result.returncode != 0:
                         # Solo sobreescribir error si hay nuevo error explicito
                         if result.stderr:
                            error_msg = result.stderr.lower() 
                
                if result.returncode != 0:
                    ret = {
                        "success": False,
                        "error": f"Error: {error_msg[:150]}",
                        "suggestion": "Intenta con otro video de Facebook"
                    }
                    if id_match_err:
                        ret['detected_id'] = id_match_err.group(1)
                    return ret

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

    def _extract_manual(self, url):
        """
        Intenta extraer el video usando requests y regex básicos para obtener og:video o 'playable_url'
        """
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }

            html = None
            # Intentar resolver redirección primero CON GET
            final_url = url
            if '/share/' in url:
                try:
                    # Usar GET en lugar de HEAD para mejor manejo de redirecciones en sitios JS
                    r_head = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
                    if r_head.url != url:
                         print(f"🔄 Redirección resuelta (manual): {url} -> {r_head.url}")
                         final_url = r_head.url
                    # Usar el contenido ya descargado si es útil
                    if 'playable_url' in r_head.text or 'og:video' in r_head.text:
                        html = r_head.text
                        scrape_url = final_url
                    else:
                        html = None
                except: 
                    html = None
                    pass

            # Si no obtuvimos HTML válido de la redirección HTTP, intentamos www directo
            if not html:
                scrape_url = final_url
                print(f"🕵️ Intentando scrape manual (www): {scrape_url}")
                r = requests.get(scrape_url, headers=headers, timeout=10)
                html = r.text
            
            # Buscar URL canónica o real en el HTML (porque FB usa redirección JS)
            # Ej: <link rel="canonical" href="https://www.facebook.com/reel/123456" />
            # Ej: <meta property="og:url" content="..." />
            canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
            if not canonical_match:
                 canonical_match = re.search(r'<meta\s+property="og:url"\s+content="([^"]+)"', html)
            
            if canonical_match:
                real_url = canonical_match.group(1).replace("&amp;", "&")
                if real_url != final_url and 'facebook.com' in real_url:
                    print(f"🔄 URL Canónica detectada: {real_url}")
                    final_url = real_url
                    # Actualizar fdown_data con la URL real si es diferente
                    url = real_url 

            # Diagnóstico: Ver si es página de login
            if 'login_form' in html or 'Inicia sesión' in html or 'Log In' in html:
                print("⚠️ Detectada página de login/bloqueo.")

            # 1. Buscar meta tag og:video
            video_url = None
            og_match = re.search(r'<meta\s+property="og:video"\s+content="([^"]+)"', html)
            if not og_match:
                 og_match = re.search(r'<meta\s+property="og:video:url"\s+content="([^"]+)"', html)
            
            if og_match:
                video_url = og_match.group(1).replace("&amp;", "&")
                print(f"✅ Encontrado og:video: {video_url[:50]}...")
            
            # 2. Si no, buscar playable_url_quality_hd en JSON incrustado
            if not video_url:
                hd_match = re.search(r'"playable_url_quality_hd":"([^"]+)"', html)
                if hd_match:
                    video_url = hd_match.group(1).replace("\\/", "/")
                    print(f"✅ Encontrado playable_url_quality_hd: {video_url[:50]}...")
            
            # 3. Si no, buscar playable_url (SD)
            if not video_url:
                sd_match = re.search(r'"playable_url":"([^"]+)"', html)
                if sd_match:
                    video_url = sd_match.group(1).replace("\\/", "/")
                    print(f"✅ Encontrado playable_url: {video_url[:50]}...")

            if video_url:
                # Extraer título y thumbnail básicos
                title_match = re.search(r'<title>(.*?)</title>', html)
                title = title_match.group(1) if title_match else "Facebook Video"
                
                thumb_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
                thumbnail = thumb_match.group(1).replace("&amp;", "&") if thumb_match else ""

                return {
                    "success": True,
                    "title": title,
                    "description": "Video extraído manualmente",
                    "duration": 0,
                    "uploader": "Facebook Generic",
                    "thumbnail": thumbnail,
                    "view_count": 0,
                    "video_url": video_url,
                    "video_quality": "Manual Extract",
                    "platform": "Facebook",
                    "formats": [{"url": video_url, "ext": "mp4"}]
                }
            
            # Fallback a m.facebook.com si www falló
            if 'm.facebook.com' not in scrape_url:
                 mobile_url = final_url.replace('www.facebook.com', 'm.facebook.com').replace('web.facebook.com', 'm.facebook.com')
                 print(f"🕵️ Reintentando scrape manual (mobile): {mobile_url}")
                 r_mobile = requests.get(mobile_url, headers=headers, timeout=10)
                 html_mobile = r_mobile.text
                 # Repetir busqueda en mobile... (simplificado para no duplicar código mucho, podríamos hacer un loop pero por ahora copy-paste logico breve)
                 # ... buscar patterns en html_mobile ...
                 # (Para no hacer el código gigante, solo checkeo un pattern comùn en mobile)
                 m_match = re.search(r'href="(/video_redirect/\?src=.*?)"', html_mobile)
                 if m_match:
                     import urllib.parse
                     raw_url = m_match.group(1)
                     # Decodificar URL
                     if 'src=' in raw_url:
                         video_url = urllib.parse.unquote(raw_url.split('src=')[1].split('&')[0])
                         print(f"✅ Encontrado video redirect mobile: {video_url[:50]}...")
                         return {
                             "success": True,
                             "title": "Facebook Video (Mobile)", "description": "", "duration": 0, "uploader": "", "thumbnail": "", "view_count": 0,
                             "video_url": video_url, "video_quality": "Mobile", "platform": "Facebook", "formats": [{"url": video_url, "ext": "mp4"}]
                         }

            # 4. ÚLTIMO RECURSO: Intentar usar fdown.net (servicio externo)
            if not video_url:
                try:
                    print("🕵️ Intentando con servicio externo (fdown.net)...")
                    fdown_url = "https://fdown.net/download.php"
                    fdown_data = {'URL': url}
                    fdown_headers = headers.copy()
                    fdown_headers['Origin'] = 'https://fdown.net'
                    fdown_headers['Referer'] = 'https://fdown.net/'
                    
                    r_fdown = requests.post(fdown_url, data=fdown_data, headers=fdown_headers, timeout=15)
                    fdown_html = r_fdown.text
                    
                    # Buscar enlace HD
                    hd_link_match = re.search(r'<a href="([^"]+)"\s+[^>]*id="hdlink"', fdown_html)
                    if hd_link_match:
                        video_url = hd_link_match.group(1).replace("&amp;", "&")
                        quality = "HD"
                        print(f"✅ Encontrado enlace fdown (HD)")
                    else:
                        # Buscar enlace SD
                        sd_link_match = re.search(r'<a href="([^"]+)"\s+[^>]*id="sdlink"', fdown_html)
                        if sd_link_match:
                            video_url = sd_link_match.group(1).replace("&amp;", "&")
                            quality = "SD"
                            print(f"✅ Encontrado enlace fdown (SD)")

                    if video_url:
                         return {
                            "success": True,
                            "title": "Facebook Video (External)",
                            "description": "Extraído vía fdown.net",
                            "duration": 0,
                            "uploader": "Facebook User",
                            "thumbnail": "",  # fdown no da thumbnail fácil
                            "view_count": 0,
                            "video_url": video_url,
                            "video_quality": quality,
                            "platform": "Facebook",
                            "formats": [{"url": video_url, "ext": "mp4"}]
                        }
                except Exception as e_ext:
                    print(f"⚠️ Fallo servicio externo: {e_ext}")

            return {
                "success": False,
                "error": "No se pudo extraer la URL del video manualmente ni con servicios externos.",
                "suggestion": "Facebook ha cambiado su estructura o requiere login."
            }

        except Exception as e:
            print(f"❌ Error en scrape manual: {e}")
            return {
                 "success": False,
                 "error": f"Error manual: {str(e)}",
                "suggestion": "Intenta con otro video"
            }
