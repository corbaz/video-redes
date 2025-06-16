#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import traceback
import logging
from urllib.parse import parse_qs, urlparse
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler

# Importar extractores
from insta_extractor import InstagramExtractor
from linkedin_extractor import LinkedInExtractor
from x_extractor import XExtractor
from tiktok_extractor import TikTokExtractor
from facebook_extractor import FacebookExtractor
from youtube_extractor import YouTubeExtractor

# Configurar logging (sin emojis para Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP Server que maneja requests en threads separados"""
    daemon_threads = True
    allow_reuse_address = True
    timeout = 60


class VideoDownloaderHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.timeout = 30
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override para usar nuestro logger"""
        logger.info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        try:
            # Filtrar requests de DevTools que no necesitamos
            if '/.well-known/' in self.path:
                self.send_error(404)
                return

            # Limpiar la ruta de parámetros de versión (?v=...)
            clean_path = self.path.split('?')[0]

            # Servir index.html para la raíz
            if clean_path == '/' or clean_path == '/index.html':
                self.serve_file('index.html')
            elif clean_path.endswith('.js'):
                filename = clean_path.lstrip('/')
                if os.path.exists(filename):
                    self.serve_file(filename)
                else:
                    self.send_error(404)
            elif clean_path.endswith('.css'):
                filename = clean_path.lstrip('/')
                if os.path.exists(filename):
                    self.serve_file(filename)
                else:
                    self.send_error(404)
            elif clean_path.endswith('.ico'):
                filename = clean_path.lstrip('/')
                if os.path.exists(filename):
                    self.serve_file(filename)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        except Exception as e:
            logger.error(f"Error en do_GET: {str(e)}")
            self.send_error(500)

    def do_POST(self):
        try:
            # Obtener el path sin el / inicial
            path = self.path.lstrip('/')

            # Manejar endpoints de API
            if path == 'api/validate':
                self.handle_validate()
            elif path == 'api/extract':
                self.handle_extract()
            else:
                logger.warning(f"Endpoint no encontrado: {path}")
                self.send_error(404)

        except Exception as e:
            logger.error(f"Error en do_POST: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_json_response(
                {'success': False, 'error': 'Error del servidor'}, 500)

    def serve_file(self, filename):
        """Sirve archivos estáticos con headers apropiados"""
        try:
            if not os.path.exists(filename):
                logger.warning(f"Archivo no encontrado: {filename}")
                self.send_error(404)
                return

            with open(filename, 'rb') as f:
                content = f.read()

            # Determinar content-type
            if filename.endswith('.html'):
                content_type = 'text/html; charset=utf-8'
            elif filename.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif filename.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif filename.endswith('.ico'):
                content_type = 'image/x-icon'
            else:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)

            logger.debug(f"Archivo servido: {filename}")

        except Exception as e:
            logger.error(f"Error sirviendo archivo {filename}: {str(e)}")
            self.send_error(500)

    def handle_validate(self):
        """Valida URLs para compatibilidad con el frontend actual"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            url = data.get('url', '').strip()
            if not url:
                self.send_json_response(
                    {'success': False, 'error': 'URL requerida'}, 400)
                return            # Validar URL según plataforma
            if any(domain in url for domain in ['instagram.com', 'linkedin.com', 'x.com', 'twitter.com', 'tiktok.com', 'facebook.com', 'fb.watch', 'youtube.com', 'youtu.be', 'm.youtube.com']):
                self.send_json_response({
                    'success': True,
                    'url': url,
                    'message': 'URL válida'
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': 'Plataforma no soportada. Usa Instagram, LinkedIn, X/Twitter, TikTok, Facebook o YouTube.'
                }, 400)

        except Exception as e:
            logger.error(f"Error en validate: {str(e)}")
            self.send_json_response({'success': False, 'error': str(e)}, 500)

    def handle_extract(self):
        """Maneja requests de extracción de video"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            url = data.get('url', '').strip()
            if not url:
                self.send_json_response(
                    {'success': False, 'error': 'URL requerida'}, 400)
                return

            logger.info(f"Extrayendo video de: {url}")

            # Determinar plataforma y extraer
            result = self.extract_video_info(url)

            if result['success']:
                # Log detallado con información de video
                platform = result.get('platform', 'Desconocida')
                title = result.get('title', 'Sin título')[:50]
                quality = result.get(
                    'quality_label', result.get('video_quality', 'N/A'))
                filesize = result.get('filesize', 'N/A')
                duration = result.get('duration', 0)

                logger.info(f"✅ Extracción exitosa para: {url}")
                logger.info(f"   📺 Plataforma: {platform}")
                logger.info(f"   🎬 Título: {title}...")
                logger.info(f"   🎯 Resolución: {quality}")
                logger.info(f"   📁 Tamaño: {filesize}")
                logger.info(f"   ⏱️ Duración: {duration}s")

                self.send_json_response(result)
            else:
                logger.warning(f"Error extrayendo {url}: {result['error']}")
                self.send_json_response(result, 400)

        except json.JSONDecodeError:
            logger.error("Error decodificando JSON del request")
            self.send_json_response(
                {'success': False, 'error': 'JSON inválido'}, 400)
        except Exception as e:
            logger.error(f"Error en handle_extract: {str(e)}")
            logger.error(traceback.format_exc())
            self.send_json_response(
                {'success': False, 'error': f'Error del servidor: {str(e)}'}, 500)

    def extract_video_info(self, url):
        """Extrae información del video según la plataforma"""
        try:
            # Detectar plataforma e inicializar extractor
            if 'instagram.com' in url:
                extractor = InstagramExtractor()
                platform = 'instagram'
            elif 'linkedin.com' in url:
                extractor = LinkedInExtractor()
                platform = 'linkedin'
            elif 'x.com' in url or 'twitter.com' in url:
                extractor = XExtractor()
                platform = 'x'
            elif 'tiktok.com' in url:
                extractor = TikTokExtractor()
                platform = 'tiktok'
            elif 'facebook.com' in url or 'fb.watch' in url:
                extractor = FacebookExtractor()
                platform = 'facebook'
            elif 'youtube.com' in url or 'youtu.be' in url or 'm.youtube.com' in url:
                extractor = YouTubeExtractor()
                platform = 'youtube'
            else:
                return {
                    'success': False,
                    'error': 'Plataforma no soportada. Usa Instagram, LinkedIn, X/Twitter, TikTok, Facebook o YouTube.'
                }

            # Extraer video usando el método extract_info del extractor
            result = extractor.extract_info(url)

            if result.get('success'):
                result['platform'] = platform
                return result
            else:
                return {
                    'success': False,
                    'error': result.get('error', f'Error extrayendo video de {platform}')
                }

        except Exception as e:
            logger.error(f"Error extrayendo video de {url}: {str(e)}")
            return {
                'success': False,
                'error': f'Error procesando URL: {str(e)}'
            }

    def send_json_response(self, data, status=200):
        """Envía respuesta JSON con headers apropiados"""
        try:
            response = json.dumps(data, ensure_ascii=False).encode('utf-8')

            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods',
                             'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            self.wfile.write(response)
        except Exception as e:
            logger.error(f"Error enviando respuesta JSON: {str(e)}")

    def do_OPTIONS(self):
        """Maneja requests CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server():
    """Inicia el servidor con configuración optimizada"""
    try:
        # Configuración del servidor
        host = '0.0.0.0'  # Escucha en todas las interfaces
        port = 8000  # Puerto estándar

        server = ThreadedHTTPServer((host, port), VideoDownloaderHandler)
        server.timeout = 60

        logger.info("=" * 60)
        logger.info("Video Downloader Server v2.2 - API Fixed")
        logger.info("=" * 60)
        logger.info(f"Servidor iniciado en http://{host}:{port}")
        logger.info(f"Acceso local: http://localhost:{port}")
        logger.info(f"Acceso red: http://192.168.1.50:{port}")
        logger.info("Endpoints disponibles:")
        logger.info("  POST /api/validate - Validar URLs")
        logger.info("  POST /api/extract - Extraer videos")
        logger.info("Presiona Ctrl+C para detener")
        logger.info("=" * 60)

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario")
    except OSError as e:
        if e.errno == 98 or "Address already in use" in str(e):
            logger.error(f"Puerto {port} ya está en uso")
            logger.info("Ejecuta: taskkill /f /im python.exe")
        else:
            logger.error(f"Error del sistema: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        logger.error(traceback.format_exc())
    finally:
        try:
            server.server_close()
            logger.info("Servidor cerrado correctamente")
        except:
            pass


if __name__ == '__main__':
    # Verificar extractores disponibles
    print("Verificando extractores...")

    try:
        from insta_extractor import InstagramExtractor
        print("Instagram extractor: OK")
    except Exception as e:
        print(f"Instagram extractor error: {e}")

    try:
        from linkedin_extractor import LinkedInExtractor
        print("LinkedIn extractor: OK")
    except Exception as e:
        print(f"LinkedIn extractor error: {e}")

    try:
        from x_extractor import XExtractor
        print("X/Twitter extractor: OK")
    except Exception as e:
        print(f"X/Twitter extractor error: {e}")

    try:
        from tiktok_extractor import TikTokExtractor
        print("TikTok extractor: OK")
    except Exception as e:
        print(f"TikTok extractor error: {e}")

    try:
        from facebook_extractor import FacebookExtractor
        print("Facebook extractor: OK")
    except Exception as e:
        print(f"Facebook extractor error: {e}")

    print()
    run_server()
