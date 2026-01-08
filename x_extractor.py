from typing import Dict, Any


class XExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae la URL directa del video de X (Twitter) usando yt-dlp y la devuelve compatible con el frontend.
        """
        try:
            print(f"🔍 Extrayendo video de X/Twitter con yt-dlp: {url}")
            import yt_dlp

            # Configurar yt-dlp para obtener la mejor calidad
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'timeout': 10,
                # Seleccionar la mejor calidad de video+audio combinada
                # Formato: mejor video + mejor audio, o mejor combinado
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',  # Asegurar salida en MP4
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Debugging: mostrar qué devuelve yt-dlp
                print(
                    f"🔍 yt-dlp returned info keys: {list(info.keys()) if info else 'None'}")

                # Buscar la URL real del video en diferentes campos
                video_url = None

                # Si hay formatos disponibles, seleccionar el de mejor calidad
                if 'formats' in info and info['formats']:
                    # Filtrar solo formatos con video
                    video_formats = [
                        fmt for fmt in info['formats']
                        if fmt.get('vcodec') != 'none' and fmt.get('url')
                    ]
                    
                    if video_formats:
                        # Ordenar por calidad (resolución y bitrate)
                        def get_quality_score(fmt):
                            # Calcular un score basado en altura, ancho y bitrate
                            height = fmt.get('height') or 0
                            width = fmt.get('width') or 0
                            tbr = fmt.get('tbr') or 0  # Total bitrate
                            
                            # Priorizar resolución, luego bitrate
                            return (height * width, tbr)
                        
                        # Ordenar de mayor a menor calidad
                        video_formats.sort(key=get_quality_score, reverse=True)
                        
                        # Tomar el de mejor calidad
                        best_format = video_formats[0]
                        video_url = best_format['url']
                        
                        resolution = f"{best_format.get('width')}x{best_format.get('height')}" if best_format.get('width') else 'unknown'
                        bitrate = f"{best_format.get('tbr')}kbps" if best_format.get('tbr') else 'unknown'
                        
                        print(f"✅ Mejor calidad encontrada: {resolution} @ {bitrate}")
                        print(f"   URL: {video_url[:50]}...")
                    else:
                        print("⚠️ No se encontraron formatos de video válidos")

                # Fallback a campos directos
                if not video_url:
                    # Asegurar que no sea la URL original
                    if 'url' in info and info['url'] != url:
                        video_url = info['url']
                    elif 'video_url' in info:
                        video_url = info['video_url']

                if video_url and video_url != url:  # Verificar que no sea la URL original
                    print(f"✅ Video extraído: {video_url[:50]}...")
                    return {
                        "success": True,
                        "data": {
                            "videoUrl": video_url,
                            "title": info.get('title', 'Video de X/Twitter'),
                            "uploader": info.get('uploader', ''),
                            "duration": info.get('duration'),
                            "thumbnail": info.get('thumbnail'),
                            "description": info.get('description', '')
                        }
                    }
                else:
                    print(
                        "❌ No se encontró URL de video válida en la respuesta de yt-dlp")
                    print(
                        f"   Campos disponibles: {list(info.keys()) if info else 'None'}")
                    return {
                        "success": False,
                        "error": "No se encontró video en esta publicación de X/Twitter"
                    }

        except Exception as e:
            print(f"❌ Error X extractor: {str(e)}")
            return {
                "success": False,
                "error": f"Error al extraer video de X/Twitter: {str(e)}"
            }
