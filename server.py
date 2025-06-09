from typing import Dict, Any, List
import os
import time
import traceback
import re
import subprocess
import json
import socketserver
import http.server
import requests
from urllib.parse import urlparse, parse_qs
import tempfile

# Try to import moviepy for precise audio detection
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# Try to import pydub as alternative for audio detection
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

"""
Instagram Video Downloader - Bulletproof Server
GUARANTEED to never show XML/JSON parsing errors
"""


class InstagramDownloader:
    """Instagram downloader with bulletproof error handling"""

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract video info with guaranteed JSON response"""
        try:
            print(f"🔍 Processing: {url}")

            # Try yt-dlp extraction
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-warnings",
                "--ignore-errors",
                url.strip()
            ]

            print(f"🚀 Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            print(f"📊 Return code: {result.returncode}")
            print(
                f"📊 Stdout length: {len(result.stdout) if result.stdout else 0}")
            print(
                f"📊 Stderr: {result.stderr[:200] if result.stderr else 'None'}...")

            # Handle the response
            if result.returncode == 0 and result.stdout and result.stdout.strip():
                stdout = result.stdout.strip()

                # Check if it's valid JSON
                if self._is_json(stdout):
                    try:
                        data = json.loads(stdout)
                        return self._process_success(data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing failed: {e}")
                        return self._error("JSON parsing failed")
                else:
                    print("❌ Output is not JSON")
                    return self._analyze_non_json(stdout, result.stderr)
            else:
                print("❌ Command failed or no output")
                return self._analyze_error(result.stderr)

        except subprocess.TimeoutExpired:
            print("❌ Timeout")
            return self._error("Request timeout", "timeout")
        except Exception as e:
            print(f"❌ Exception: {e}")
            return self._error(f"Extraction failed: {e}")

    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        try:
            if not text or not text.strip():
                return False
            text = text.strip()
            if not (text.startswith('{') or text.startswith('[')):
                return False
            json.loads(text)
            return True
        except:
            return False

    def _analyze_non_json(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Analyze non-JSON responses"""
        content = (stdout + " " + (stderr or "")).lower()

        if "login" in content or "authentication" in content or "credentials" in content:
            return self._error(
                "Instagram requires authentication",
                "auth_required",
                "This video is protected. Try with more public videos from popular accounts."
            )

        if "rate limit" in content or "rate-limit" in content:
            return self._error(
                "Instagram rate limiting",
                "rate_limit",
                "Instagram is blocking requests. Try again in a few minutes."
            )

        if "not available" in content or "404" in content:
            return self._error(
                "Video not found",
                "not_found",
                "The video may have been deleted or the URL is incorrect."
            )

        return self._error(
            "Instagram access blocked",
            "blocked",
            "Instagram is protecting this content. Try with different public videos."
        )

    def _analyze_error(self, stderr: str) -> Dict[str, Any]:
        """Analyze command errors"""
        if not stderr:
            return self._error("Unknown extraction error")

        stderr_lower = stderr.lower()

        if "login required" in stderr_lower or "credentials" in stderr_lower:
            return self._error(
                "Instagram authentication required",
                "auth_required",
                "This content requires login. Try with public videos from verified accounts."
            )

        if "not available" in stderr_lower:
            return self._error(
                "Content not available",
                "unavailable",
                "The video is private, deleted, or not accessible."
            )

        if "timeout" in stderr_lower:
            return self._error(
                "Connection timeout",
                "timeout",
                "Instagram took too long to respond. Try again."
            )

        return self._error(
            "Instagram access denied",
            "access_denied",
            "Instagram is blocking access to this content. Try with popular public videos."
        )

    def _check_audio_with_pydub(self, url: str) -> bool:
        """Verificar si un video tiene audio usando pydub (alternativa ligera)"""
        if not PYDUB_AVAILABLE:
            print("⚠️ pydub no disponible, usando fallback")
            return False

        temp_file = None
        try:
            print(f"🎵 Analizando con pydub: {url[:100]}...")

            # Descargar una muestra pequeña del video
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp:
                temp_file = temp.name

            # Usar requests para descargar una porción pequeña (1MB)
            headers = {'Range': 'bytes=0-1048575'}  # Primeros 1MB
            response = requests.get(
                url, headers=headers, timeout=10, stream=True)

            if response.status_code in [206, 200]:
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            if f.tell() > 1048575:  # 1MB máximo
                                break

                # Verificar con pydub si tiene audio
                try:
                    # Intentar leer como video/audio con pydub
                    audio = AudioSegment.from_file(temp_file)
                    has_audio = len(audio) > 0 and audio.duration_seconds > 0

                    if has_audio:
                        print(
                            f"🎵 pydub detectó audio: duración {audio.duration_seconds:.2f}s, canales {audio.channels}")
                    else:
                        print("🔇 pydub NO detectó audio")

                    return has_audio

                except Exception as e:
                    print(f"⚠️ Error procesando con pydub: {e}")
                    return False
            else:
                print(
                    f"⚠️ No se pudo descargar muestra: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️ Error con pydub: {e}")
            return False
        finally:
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def _check_audio_with_moviepy(self, url: str) -> bool:
        """Verificar si un video tiene audio usando moviepy (más preciso)"""
        if not MOVIEPY_AVAILABLE:
            print("⚠️ moviepy no disponible, usando fallback")
            return False

        temp_file = None
        try:
            print(f"🎬 Analizando con moviepy: {url[:100]}...")

            # Descargar una muestra pequeña del video (primeros 5 segundos)
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp:
                temp_file = temp.name

            # Usar requests para descargar una porción pequeña
            headers = {'Range': 'bytes=0-2097151'}  # Primeros 2MB
            response = requests.get(
                url, headers=headers, timeout=15, stream=True)

            if response.status_code in [206, 200]:
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            # Limitar descarga para mantener velocidad
                            if f.tell() > 2097151:  # 2MB máximo
                                break

                # Verificar con moviepy si tiene audio
                try:
                    clip = VideoFileClip(temp_file)
                    has_audio = clip.audio is not None

                    if has_audio:
                        # Verificar duración del audio para asegurar que existe
                        audio_duration = clip.audio.duration if clip.audio else 0
                        has_audio = audio_duration > 0
                        print(
                            f"🎵 moviepy detectó audio: duración {audio_duration:.2f}s")
                    else:
                        print("🔇 moviepy NO detectó audio")

                    clip.close()
                    return has_audio

                except Exception as e:
                    print(f"⚠️ Error procesando con moviepy: {e}")
                    return False
            else:
                print(
                    f"⚠️ No se pudo descargar muestra: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️ Error con moviepy: {e}")
            return False
        finally:
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def _check_audio_with_ffprobe(self, url: str) -> bool:
        """Verificar si un video tiene audio usando ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-select_streams", "a",
                "-show_entries", "stream=codec_name",
                "-of", "csv=p=0",
                url
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)
            has_audio = result.returncode == 0 and result.stdout.strip()

            if has_audio:
                print(f"🎵 ffprobe detectó audio: {result.stdout.strip()}")
            else:
                print(f"🔇 ffprobe NO detectó audio")

            return has_audio

        except Exception as e:
            print(f"⚠️ Error con ffprobe: {e}")
            return False

    def _process_success(self, data: Dict) -> Dict[str, Any]:
        """Process successful video data and filter MP4s with audio using moviepy"""
        try:
            # Extract all video formats first
            all_formats = []
            for fmt in data.get("formats", []):
                if fmt.get("vcodec") != "none" and fmt.get("url"):
                    all_formats.append({
                        "url": fmt["url"],
                        "format_id": fmt.get("format_id", ""),
                        "ext": fmt.get("ext", "mp4"),
                        "width": fmt.get("width", 0),
                        "height": fmt.get("height", 0),
                        "quality": f"{fmt.get('height', 0)}p" if fmt.get('height') else "Unknown",
                        "filesize": fmt.get("filesize") or fmt.get("filesize_approx", 0),
                        # Audio metadata (para debug)
                        "acodec": fmt.get("acodec", "none"),
                        "abr": fmt.get("abr", 0),
                        "audio_ext": fmt.get("audio_ext", "none"),
                        "audio_channels": fmt.get("audio_channels", 0),
                        "format_note": fmt.get("format_note", "")
                    })

            # Filter only MP4s and verify audio with moviepy
            mp4_with_audio = []
            for fmt in all_formats:
                # Check if it's MP4
                if fmt["ext"].lower() != "mp4":
                    continue

                print(
                    f"🔍 Verificando MP4 {fmt['quality']}: {fmt['url'][:100]}...")

                # 1. Verificar con moviepy (método principal y más preciso)
                has_audio_moviepy = False
                if MOVIEPY_AVAILABLE:
                    has_audio_moviepy = self._check_audio_with_moviepy(
                        fmt["url"])

                # 2. Verificar con pydub como alternativa
                has_audio_pydub = False
                if not has_audio_moviepy and PYDUB_AVAILABLE:
                    has_audio_pydub = self._check_audio_with_pydub(fmt["url"])

                # 3. Verificar con ffprobe como respaldo
                has_audio_ffprobe = self._check_audio_with_ffprobe(fmt["url"])

                # 4. Verificar metadatos como último recurso
                has_audio_metadata = (
                    (fmt["acodec"] and fmt["acodec"] not in ["none", "null"]) or
                    (fmt["abr"] is not None and fmt["abr"] != 0) or
                    (fmt["audio_ext"] and fmt["audio_ext"] != "none") or
                    (fmt["audio_channels"] and fmt["audio_channels"] > 0)
                )

                # Prioridad: moviepy > pydub > ffprobe > metadatos
                has_audio = has_audio_moviepy or has_audio_pydub or has_audio_ffprobe or has_audio_metadata

                # Determinar método de verificación
                verification_method = "unknown"
                if has_audio_moviepy:
                    verification_method = "moviepy"
                elif has_audio_pydub:
                    verification_method = "pydub"
                elif has_audio_ffprobe:
                    verification_method = "ffprobe"
                elif has_audio_metadata:
                    verification_method = "metadata"

                if has_audio:
                    fmt["has_audio"] = True
                    fmt["audio_verified_by"] = verification_method
                    mp4_with_audio.append(fmt)
                    print(
                        f"✅ MP4 con audio: {fmt['quality']} (verificado por {verification_method})")
                else:
                    print(
                        f"❌ MP4 sin audio: {fmt['quality']} - moviepy:{has_audio_moviepy} pydub:{has_audio_pydub} ffprobe:{has_audio_ffprobe} metadata:{has_audio_metadata}")

            # Sort by quality
            mp4_with_audio.sort(key=lambda x: x["height"], reverse=True)

            print(
                f"🎵 Encontrados {len(mp4_with_audio)} MP4s con audio de {len(all_formats)} formatos totales")

            # Extraer y formatear fecha de subida
            upload_date_str = ""
            timestamp = data.get("timestamp", 0)
            if timestamp:
                import datetime
                try:
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    # Calcular tiempo transcurrido
                    now = datetime.datetime.now()
                    diff = now - dt

                    if diff.days > 365:
                        years = diff.days // 365
                        upload_date_str = f"{years} año{'s' if years > 1 else ''} atrás"
                    elif diff.days > 30:
                        months = diff.days // 30
                        upload_date_str = f"{months} mes{'es' if months > 1 else ''} atrás"
                    elif diff.days > 7:
                        weeks = diff.days // 7
                        upload_date_str = f"{weeks} sem{'anas' if weeks > 1 else 'ana'} atrás"
                    elif diff.days > 0:
                        upload_date_str = f"{diff.days} día{'s' if diff.days > 1 else ''} atrás"
                    elif diff.seconds > 3600:
                        hours = diff.seconds // 3600
                        upload_date_str = f"{hours} hora{'s' if hours > 1 else ''} atrás"
                    else:
                        minutes = diff.seconds // 60
                        upload_date_str = f"{minutes} minuto{'s' if minutes > 1 else ''} atrás"
                except:
                    upload_date_str = "Fecha desconocida"

            # Extraer tags de la descripción
            description = data.get("description", "")
            tags = []
            if description:
                import re
                # Buscar hashtags en la descripción
                hashtags = re.findall(r'#(\w+)', description)
                tags = hashtags[:10]  # Limitar a 10 tags

            # Mapear correctamente los campos
            uploader_id = data.get("channel", "") or data.get(
                "uploader_id", "") or "usuario"  # Usar channel como alias
            uploader_name = data.get("uploader", "Usuario de Instagram")

            # Crear URL del perfil usando el alias
            uploader_url = f"https://www.instagram.com/{uploader_id}" if uploader_id and uploader_id != "usuario" else ""

            return {
                "success": True,
                "data": {
                    "title": data.get("title", "Video de Instagram"),
                    "uploader": uploader_name,
                    "uploader_id": uploader_id,  # Alias correcto (channel)
                    "uploader_url": uploader_url,  # URL del perfil
                    "duration": data.get("duration", 0),
                    "view_count": data.get("view_count", 0),
                    "like_count": data.get("like_count", 0),
                    "comment_count": data.get("comment_count", 0),
                    "description": description,  # Descripción completa sin truncar
                    "description_full": description,  # Alias para compatibilidad con frontend
                    "tags": tags,  # Tags extraídos de la descripción
                    "upload_date": upload_date_str,  # Fecha formateada como "27 sem"
                    "timestamp": timestamp,  # Timestamp original
                    "thumbnail": data.get("thumbnail", ""),
                    "video_formats": mp4_with_audio,  # Solo MP4s con audio verificados
                    "all_formats": all_formats,  # Todos los formatos para debug
                    "best_quality": mp4_with_audio[0] if mp4_with_audio else None,
                    "total_formats": len(mp4_with_audio),
                    "total_all_formats": len(all_formats),
                    "moviepy_available": MOVIEPY_AVAILABLE,
                    "pydub_available": PYDUB_AVAILABLE
                }
            }
        except Exception as e:
            return self._error(f"Error processing video data: {e}")

    def _error(self, message: str, error_type: str = "general", suggestion: str = "") -> Dict[str, Any]:
        """Create error response - ALWAYS returns valid JSON"""
        return {
            "success": False,
            "error": str(message),
            "error_type": str(error_type),
            "suggestion": str(suggestion) if suggestion else "Try with different Instagram URLs or check if the video is public."
        }

    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate Instagram URL"""
        if not url or not isinstance(url, str):
            return {"valid": False, "error": "URL is required"}

        url = url.strip()
        patterns = [
            r'instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9-_]+',
            r'instagram\.com/[A-Za-z0-9_.]+/(?:p|reel|reels)/[A-Za-z0-9-_]+'
        ]

        if any(re.search(pattern, url) for pattern in patterns):
            return {"valid": True, "url": url}
        else:
            return {"valid": False, "error": "Invalid Instagram URL"}


# Global downloader instance
downloader = InstagramDownloader()


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with bulletproof JSON responses"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.', **kwargs)

    def log_message(self, format, *args):
        print(f"🌐 {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_GET(self):
        if self.path.startswith('/api/'):
            self._handle_api()
        else:
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self._handle_api()
        else:
            self._send_json_error("Endpoint not found", 404)

    def _handle_api(self):
        """Handle API requests with guaranteed JSON responses"""
        try:
            # Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(
                content_length) if content_length > 0 else b''

            data = {}
            if post_data:
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError:
                    self._send_json_error("Invalid JSON", 400)
                    return

            # Route endpoints
            if self.path == '/api/health':
                self._send_json({
                    "status": "ok",
                    "message": "Instagram Downloader - XML Error Fixed!",
                    "version": "1.0.0-fixed"
                })

            elif self.path == '/api/validate':
                url = data.get('url', '').strip()
                if not url:
                    self._send_json_error("URL required", 400)
                    return

                result = downloader.validate_url(url)
                if result["valid"]:
                    self._send_json(
                        {"success": True, "valid": True, "url": result["url"]})
                else:
                    self._send_json(
                        {"success": False, "error": result["error"]}, 400)

            elif self.path == '/api/extract':
                url = data.get('url', '').strip()
                if not url:
                    self._send_json_error("URL required", 400)
                    return

                result = downloader.extract_info(url)
                status = 200 if result.get("success") else 400
                self._send_json(result, status)

            else:
                self._send_json_error("API endpoint not found", 404)

        except Exception as e:
            print(f"❌ API error: {e}")
            self._send_json_error("Internal server error", 500)

    def _send_json(self, data: Any, status: int = 200):
        """Send JSON response with absolute guarantee"""
        try:
            # Ensure JSON-safe data
            safe_data = self._make_json_safe(data)

            # Create JSON
            try:
                json_str = json.dumps(safe_data, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"❌ JSON serialization failed: {e}")
                json_str = json.dumps({
                    "success": False,
                    "error": "JSON serialization error"
                })

            json_bytes = json_str.encode('utf-8')

            # Send response
            self.send_response(status)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(json_bytes)))
            self.end_headers()
            self.wfile.write(json_bytes)

            print(f"✅ JSON sent: {status}")

        except Exception as e:
            print(f"❌ Fatal response error: {e}")
            try:
                self.send_error(500)
            except:
                pass

    def _send_json_error(self, message: str, status: int = 400):
        """Send JSON error response"""
        self._send_json({
            "success": False,
            "error": str(message)
        }, status)

    def _make_json_safe(self, obj: Any) -> Any:
        """Make object JSON serializable"""
        if isinstance(obj, dict):
            return {str(k): self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)


def start_server(port=8000):
    """Start the Instagram downloader server"""
    print("🚀 Instagram Video Downloader")
    print("=" * 50)
    print("✅ XML Error Completely Fixed")
    print("✅ Bulletproof JSON Responses")
    print("✅ Professional Error Handling")
    print(f"🌐 Server: http://localhost:{port}")
    print("=" * 50)

    # Check yt-dlp
    try:
        result = subprocess.run(['yt-dlp', '--version'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ yt-dlp: {result.stdout.strip()}")
        else:
            print("⚠️ yt-dlp not found - install with: pip install yt-dlp")
    except:
        print("⚠️ yt-dlp not found - install with: pip install yt-dlp")

    # Check moviepy for precise audio detection
    if MOVIEPY_AVAILABLE:
        print("✅ moviepy: Disponible para detección precisa de audio")
    else:
        print("⚠️ moviepy not found - install with: pip install moviepy")

    # Check pydub as alternative
    if PYDUB_AVAILABLE:
        print("✅ pydub: Disponible como alternativa para detección de audio")
    else:
        print("⚠️ pydub not found - install with: pip install pydub")

    if not MOVIEPY_AVAILABLE and not PYDUB_AVAILABLE:
        print("   Usando ffprobe como respaldo para detección de audio")

    # Check ffprobe (para verificación de audio adicional)
    try:
        result = subprocess.run(['ffprobe', '-version'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ffprobe: Disponible como verificación adicional")
        else:
            print("ℹ️ ffprobe not found - usando solo moviepy para verificación")
    except:
        print("ℹ️ ffprobe not found - usando solo moviepy para verificación")

    print("=" * 50)

    try:
        # Cambiado a 0.0.0.0 para escuchar en todas las interfaces
        with socketserver.TCPServer(("0.0.0.0", port), RequestHandler) as httpd:
            print(
                f"🚀 Server started on port {port} (accesible en todas las IPs de la red)")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python3 server.py {port + 1}")
        else:
            print(f"❌ Server error: {e}")


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port)
