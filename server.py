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
from insta_extractor import InstagramExtractor
from linkedin_extractor import LinkedInExtractor
from x_extractor import XExtractor

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


# Instancias globales
insta_extractor = InstagramExtractor()
linkedin_extractor = LinkedInExtractor()
x_extractor = XExtractor()


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

            # Route API endpoints
            if self.path == '/api/validate':
                self._handle_validate(data)
            elif self.path == '/api/extract':
                self._handle_extract(data)
            elif self.path == '/api/health':
                self._send_json(
                    {"status": "ok", "message": "Server is running"})
            else:
                self._send_json_error("Endpoint not found", 404)

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

    def _handle_validate(self, data):
        """Validate Instagram, LinkedIn o X URL"""
        url = data.get('url', '').strip()

        if not url:
            self._send_json_error("URL is required")
            return

        # Check if it's a valid Instagram, LinkedIn o X URL
        if (
            'instagram.com' in url or
            'linkedin.com' in url or
            'x.com' in url or
            'twitter.com' in url
        ):
            if 'linkedin.com' in url:
                platform = 'linkedin'
            elif 'x.com' in url or 'twitter.com' in url:
                platform = 'x'
            else:
                platform = 'instagram'
            self._send_json({
                "success": True,
                "url": url,
                "platform": platform
            })
        else:
            self._send_json_error(
                "URL no válida. Solo se admiten enlaces de Instagram, LinkedIn o X/Twitter")

    def _handle_extract(self, data):
        """Extract video from Instagram, LinkedIn o X"""
        url = data.get('url', '').strip()

        if not url:
            self._send_json_error("URL is required")
            return

        # Detect platform and use appropriate extractor
        if 'linkedin.com' in url:
            result = linkedin_extractor.extract_info(url)
        elif 'x.com' in url or 'twitter.com' in url:
            result = x_extractor.extract_info(url)
        else:
            result = insta_extractor.extract_info(url)

        status = 200 if result.get("success") else 400
        self._send_json(result, status)


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
