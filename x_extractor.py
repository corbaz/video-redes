from typing import Dict, Any


class XExtractor:
    def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae la URL directa del video de X (Twitter) usando yt-dlp y la devuelve compatible con el frontend.
        """
        try:
            print(f"🔍 Extrayendo video de X/Twitter con yt-dlp: {url}")
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'timeout': 10
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Debugging: mostrar qué devuelve yt-dlp
                print(
                    f"🔍 yt-dlp returned info keys: {list(info.keys()) if info else 'None'}")

                # Buscar la URL real del video en diferentes campos
                video_url = None

                # Si hay formatos disponibles, usar el mejor
                if 'formats' in info and info['formats']:
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none' and fmt.get('url'):
                            video_url = fmt['url']
                            print(
                                f"✅ Found video in formats: {video_url[:50]}...")
                            break

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
                            "videoUrl": video_url
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
