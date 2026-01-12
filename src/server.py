#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import traceback
import logging
from urllib.parse import parse_qs, urlparse, unquote
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import subprocess
import uuid
import imageio_ffmpeg
from yt_dlp import YoutubeDL
import threading
import mimetypes
import zipfile

# Importar extractores
from instagram.insta_extractor import InstagramExtractor
from linkedin.linkedin_extractor import LinkedInExtractor
from x.x_extractor import XExtractor
from tiktok.tiktok_extractor import TikTokExtractor
from facebook.facebook_extractor import FacebookExtractor
from youtube.youtube_extractor import YouTubeExtractor
from twitch.twitch_extractor import TwitchExtractor
from pinterest.pinterest_extractor import PinterestExtractor

# Fix Windows Unicode Output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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


# Global dictionary to store download tasks
download_tasks = {}

class VideoDownloaderHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.timeout = 60
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
            
            # Parsear query params
            query = urlparse(self.path).query
            params = parse_qs(query)

            # Servir index.html para la raíz
            if clean_path == '/' or clean_path == '/index.html':
                self.serve_file('index.html')
            elif clean_path.endswith(('.js', '.css', '.ico')):
                filename = clean_path.lstrip('/')
                self.serve_file(filename)
            
            # API Endpoints
            elif clean_path == '/api/download_start':
                # Generate Task ID and start thread
                url = params.get('url', [''])[0]
                filename = params.get('filename', ['video.mp4'])[0]
                
                if not url:
                    self.send_json_response({'error': 'URL required'}, 400)
                    return
                
                task_id = str(uuid.uuid4())
                download_tasks[task_id] = {
                    'status': 'starting',
                    'progress': 0,
                    'file_path': None,
                    'filename': filename,
                    'error': None
                }
                
                # Start background thread
                thread = threading.Thread(target=self.process_download_task, args=(task_id, url, filename))
                thread.daemon = True
                thread.start()
                
                self.send_json_response({'task_id': task_id})

            elif clean_path == '/api/download_cancel':
                task_id = params.get('id', [''])[0]
                if task_id in download_tasks:
                    download_tasks[task_id]['status'] = 'cancelled'
                    download_tasks[task_id]['error'] = 'Descarga cancelada por el usuario'
                    self.send_json_response({'status': 'cancelled'})
                else:
                    self.send_json_response({'error': 'Task not found'}, 404)

            elif clean_path == '/api/download_status':
                task_id = params.get('id', [''])[0]
                if task_id in download_tasks:
                    self.send_json_response(download_tasks[task_id])
                else:
                    self.send_json_response({'error': 'Task not found'}, 404)
            
            elif clean_path == '/api/download_file':
                task_id = params.get('id', [''])[0]
                if task_id in download_tasks and download_tasks[task_id]['status'] == 'completed':
                    file_path = download_tasks[task_id]['file_path']
                    filename = download_tasks[task_id]['filename']
                    
                    if os.path.exists(file_path):
                        self.serve_downloaded_file(file_path, filename)
                    else:
                        self.send_error(404, "File not found on server")
                else:
                    self.send_error(404, "Download not ready")

            # Legacy/Direct download (keep for fallback)
            elif clean_path == '/api/download':
                self.handle_download()
            else:
                self.send_error(404)

        except Exception as e:
            logger.error(f"Error en do_GET: {str(e)}")
            self.send_error(500)

    def process_download_task(self, task_id, url, filename):
        temp_dir = "temp_downloads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        try:
            download_tasks[task_id]['status'] = 'downloading'
            
            # Progress Hook for yt-dlp
            def progress_hook(d):
                # Check for cancellation
                if download_tasks.get(task_id, {}).get('status') == 'cancelled':
                    raise Exception('DownloadCancelled')

                if d['status'] == 'downloading':
                    try:
                        # Improved percentage calculation
                        if d.get('total_bytes') and d.get('downloaded_bytes'):
                           p = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        elif d.get('total_bytes_estimate') and d.get('downloaded_bytes'):
                           p = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                        else:
                           # Fallback to string parsing, removing ANSI codes if present
                           p_str = d.get('_percent_str', '0%').replace('%','')
                           # Remove potential ANSI color codes like \x1b[0;94m
                           import re
                           ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                           p = ansi_escape.sub('', p_str)

                        download_tasks[task_id]['progress'] = float(p)
                    except Exception as e: 
                        pass
                elif d['status'] == 'finished':
                     download_tasks[task_id]['status'] = 'download_complete'
                     download_tasks[task_id]['progress'] = 100

            # Post-processor Hook
            def pp_hook(d):
                if d['status'] == 'started':
                    download_tasks[task_id]['status'] = 'processing'
                    download_tasks[task_id]['progress'] = 0

            # ------------------------------------------------------------------
            # Gallery Download Logic (JSON List of URLs)
            # ------------------------------------------------------------------
            is_gallery = False
            gallery_urls = []
            try:
                # Basic check to avoid json.loads on normal URLs
                # JS encoded arrays might start with %5B or just be [ if decoded
                if url.strip().startswith('[') and 'http' in url:
                    gallery_urls = json.loads(url)
                    if isinstance(gallery_urls, list) and len(gallery_urls) > 0:
                        is_gallery = True
            except:
                pass
                
            if is_gallery:
                logger.info(f"📦 Processing Gallery Download: {len(gallery_urls)} items")
                # Ensure base filename doesn't have extension
                base_name = os.path.splitext(filename)[0]
                zip_filename = f"{base_name}.zip"
                zip_path = os.path.join(temp_dir, zip_filename)
                
                downloaded_files = []
                total_items = len(gallery_urls)
                
                try:
                    for idx, img_url in enumerate(gallery_urls):
                        if download_tasks.get(task_id, {}).get('status') == 'cancelled':
                             raise Exception('DownloadCancelled')
                             
                        # Determine extension
                        parsed_url = urlparse(img_url)
                        ext = os.path.splitext(parsed_url.path)[1]
                        if not ext: ext = ".jpg"
                        
                        # Naming: base-1.jpg, base-2.jpg ...
                        item_filename = f"{base_name}-{idx+1}{ext}"
                        item_path = os.path.join(temp_dir, item_filename)
                        
                        # Download item
                        # Use generic headers or platform specific if needed
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                        
                        # Special handling for X/Twitter/LinkedIn if needed
                        if 'twimg.com' in img_url:
                             pass 
                        
                        r = requests.get(img_url, stream=True, headers=headers, timeout=30)
                        
                        if r.status_code == 200:
                            with open(item_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk: f.write(chunk)
                            downloaded_files.append((item_path, item_filename))
                        else:
                            logger.warning(f"Failed to download gallery item {idx}: {img_url} ({r.status_code})")
                        
                        # Update progress
                        progress = int(((idx + 1) / total_items) * 90) # Leave 10% for zipping
                        download_tasks[task_id]['progress'] = progress
                    
                    # Create Zip
                    if downloaded_files:
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for file_p, file_n in downloaded_files:
                                zipf.write(file_p, file_n)
                        
                        # Cleanup individual files
                        for file_p, _ in downloaded_files:
                            try:
                                os.remove(file_p)
                            except:
                                pass
                                
                        download_tasks[task_id]['file_path'] = zip_path
                        download_tasks[task_id]['filename'] = zip_filename
                        download_tasks[task_id]['status'] = 'completed'
                        download_tasks[task_id]['progress'] = 100
                        return
                    else:
                        raise Exception("No images could be downloaded from gallery")
                        
                except Exception as e:
                     logger.error(f"Gallery download error: {str(e)}")
                     raise e

            # Validar e iniciar descarga similar a handle_download pero actualizando task
            # Detectar si es una imagen o documento (PDF) por la extensión solicitada
            is_direct_download = any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf'])
            
            is_supported_hq = any(d in url for d in ['youtube.com', 'youtu.be', 'tiktok.com', 'vm.tiktok.com', 'twitch.tv', 'pinterest.com', 'pin.it', 'pinimg.com', 'linkedin.com', 'facebook.com', 'fb.watch', 'twitter.com', 'x.com', 'instagram.com', 'cdninstagram.com', 'twimg.com'])
            
            if is_supported_hq and not is_direct_download:
                unique_id = str(uuid.uuid4())
                filename_base = f"yt_{unique_id}"
                
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': ffmpeg_exe,
                    'outtmpl': os.path.join(temp_dir, f"{filename_base}.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'progress_hooks': [progress_hook],
                    'postprocessor_hooks': [pp_hook],
                    # Smart audio handling - convert only if needed by container, otherwise copy
                    # Removed forced AAC encoding to speed up transcoding
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    # 'postprocessor_args': {'ffmpeg': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']} # REMOVED FOR SPEED
                }
                
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    # Retry logic for Instagram Private/Stories
                    is_insta_issue = 'instagram.com' in url and ('stories' in url or 'private' in str(e).lower() or 'user info' in str(e).lower())
                    
                    if is_insta_issue:
                        logger.info("⚠️ Instagram download failed. Retrying with Chrome cookies...")
                        ydl_opts['cookiesfrombrowser'] = ('chrome', )
                        try:
                            with YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])
                        except Exception as e2:
                            logger.info("⚠️ Chrome cookies failed. Retrying with Edge cookies...")
                            ydl_opts['cookiesfrombrowser'] = ('edge', )
                            with YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])
                    else:
                        raise e
                
                # Encontrar archivo
                final_path = os.path.join(temp_dir, f"{filename_base}.mp4")
                if not os.path.exists(final_path):
                     files = [f for f in os.listdir(temp_dir) if f.startswith(filename_base)]
                     if files: final_path = os.path.join(temp_dir, files[0])
                
                if os.path.exists(final_path):
                     download_tasks[task_id]['file_path'] = final_path
                     download_tasks[task_id]['status'] = 'completed'
                     download_tasks[task_id]['progress'] = 100
                else:
                     raise Exception("File not found after download")

            else:
                # Manejo de imágenes, PDFs o fallbacks
                if is_direct_download:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(url, stream=True, headers=headers, timeout=60)
                    if r.status_code == 200:
                        file_path = os.path.join(temp_dir, filename)
                        total_length = r.headers.get('content-length')
                        dl = 0
                        with open(file_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if download_tasks.get(task_id, {}).get('status') == 'cancelled':
                                    r.close()
                                    raise Exception('DownloadCancelled')
                                f.write(chunk)
                                dl += len(chunk)
                                if total_length:
                                    download_tasks[task_id]['progress'] = int(dl * 100 / int(total_length))
                        
                        download_tasks[task_id]['file_path'] = file_path
                        download_tasks[task_id]['status'] = 'completed'
                        download_tasks[task_id]['progress'] = 100
                    else:
                        raise Exception(f"Error descargando imagen: {r.status_code}")

                else:
                    # Legacy Requests fallback
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.linkedin.com/' 
                    }
                    
                    logger.info(f"Fallback download via requests: {url}")
                    r = requests.get(url, stream=True, headers=headers, timeout=60)
                    
                    if r.status_code != 200:
                        logger.error(f"Failed to download: {r.status_code}")
                        raise Exception(f"Error descarga HTTP: {r.status_code}")
                    # Determinar extensión basada en el nombre de archivo solicitado
                    ext = os.path.splitext(filename)[1]
                    if not ext: ext = ".mp4"
                    final_path = os.path.join(temp_dir, f"direct_{task_id}{ext}")
                    
                    total_length = r.headers.get('content-length')
                    dl = 0
                    with open(final_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if download_tasks.get(task_id, {}).get('status') == 'cancelled':
                                r.close()
                                raise Exception('DownloadCancelled')
                            if chunk:
                                dl += len(chunk)
                                f.write(chunk)
                                if total_length:
                                    download_tasks[task_id]['progress'] = int(dl * 100 / int(total_length))
                    
                    download_tasks[task_id]['file_path'] = final_path
                    download_tasks[task_id]['status'] = 'completed'
        
        except Exception as e:
            if str(e) == 'DownloadCancelled':
                logger.info(f"Tarea {task_id} cancelada.")
            else:
                logger.error(f"Task error {task_id}: {e}")
                download_tasks[task_id]['status'] = 'error'
                download_tasks[task_id]['error'] = str(e)

    def serve_downloaded_file(self, path, filename):
         try:
            # Snyk Path Validation
            safe_base = os.path.realpath(os.getcwd())
            requested_path = os.path.realpath(path)
            
            if os.path.commonpath([safe_base, requested_path]) != safe_base:
                 logger.warning(f"⛔ Attempt to serve file outside base: {path}")
                 self.send_error(403)
                 return
            
            with open(requested_path, 'rb') as f:
                self.send_response(200)
                # Adivinar MIME type
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type: content_type = 'application/octet-stream'
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(os.path.getsize(requested_path)))
                self.end_headers()
                while True:
                    chunk = f.read(8192)
                    if not chunk: break
                    self.wfile.write(chunk)
         except Exception as e:
            logger.error(f"Error serving file: {e}")

    def handle_download(self):
        """Descarga video usando pytubefix para YouTube (720p+) o proxy para otros"""
        temp_dir = "temp_downloads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        try:
            # Parsear query params
            query = urlparse(self.path).query
            params = parse_qs(query)
            
            url = params.get('url', [''])[0]
            filename = params.get('filename', ['video.mp4'])[0]

            # SSRF Protection: Validate protocol and host
            parsed_download = urlparse(url)
            if parsed_download.scheme not in ('http', 'https'):
                self.send_error(400, "Protocolo no soportado (SSRF Protection)")
                return
            
            # Simple hostname blocklist for local dev env
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
            if parsed_download.hostname in blocked_hosts or (parsed_download.hostname and parsed_download.hostname.startswith('192.168.')):
                 self.send_error(403, "Acceso a red local no permitido (SSRF Protection)")
                 return
            
            logger.info(f"📥 Solicitud de descarga recibida:")
            logger.info(f"   🔗 URL: {url[:100]}...")
            logger.info(f"   📄 Filename: {filename}")
            
            if not url:
                self.send_error(400, "URL requerida")
                return

            # Detectar si es YouTube para usar yt-dlp CLI
            # IMPORTANTE: Los links de googlevideo.com NO son links de YouTube válidos para yt-dlp HQ.
            # Necesitamos la URL original de YouTube.
            # Detectar si es YouTube o TikTok (ambos soportados por yt-dlp para mejor calidad)
            # Detectar si es YouTube o TikTok (ambos soportados por yt-dlp para mejor calidad)
            # IMPORTANTE: Los links de googlevideo.com NO son links de YouTube válidos para yt-dlp HQ.
            is_supported_hq = any(d in url for d in ['youtube.com', 'youtu.be', 'tiktok.com', 'vm.tiktok.com', 'twitch.tv', 'pinterest.com', 'pin.it', 'pinimg.com', 'instagram.com', 'cdninstagram.com'])
            
            # Detectar si es una imagen
            is_image = any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
            
            if is_supported_hq and not is_image:
                logger.info(f"🚀 Iniciando descarga HQ con librerías para: {url[:100]}...")
                
                # Configuración de salida
                unique_id = str(uuid.uuid4())
                filename_base = f"yt_{unique_id}"
                final_path = os.path.join(temp_dir, f"{filename_base}.mp4")
                
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

                # Opciones para la librería YoutubeDL
                # Opciones para la librería YoutubeDL
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': ffmpeg_exe,
                    'outtmpl': os.path.join(temp_dir, f"{filename_base}.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    # Smart audio handling - convert only if needed by container, otherwise copy
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    # Removed forced AAC encoding to speed up transcoding
                    # 'postprocessor_args': {'ffmpeg': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']}
                }

                try:
                    try:
                        with YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                    except Exception as e:
                        # Retry logic for Instagram Private/Stories
                        is_insta_issue = 'instagram.com' in url and ('stories' in url or 'private' in str(e).lower() or 'user info' in str(e).lower())
                        
                        if is_insta_issue:
                            logger.info("⚠️ Instagram download failed. Retrying with Chrome cookies...")
                            ydl_opts['cookiesfrombrowser'] = ('chrome', )
                            try:
                                with YoutubeDL(ydl_opts) as ydl:
                                    ydl.download([url])
                            except Exception as e2:
                                logger.info("⚠️ Chrome cookies failed. Retrying with Edge cookies...")
                                # On Windows, ensure Edge is not running or use --cookies-from-browser edge
                                # Sometimes 'permission denied' happens if browser is open.
                                # Try a fallback to 'firefox' if available or just log error.
                                try:
                                    ydl_opts['cookiesfrombrowser'] = ('edge', )
                                    with YoutubeDL(ydl_opts) as ydl:
                                        ydl.download([url])
                                except Exception as e3:
                                    # If both failed and it's a permission/copy error, raise a clear message
                                    err_str = str(e3).lower()
                                    if "could not copy" in err_str or "permission denied" in err_str:
                                        raise Exception("BROWSER_LOCK_ERROR: Cierra Chrome/Edge para permitir el acceso a las cookies.")
                                    raise e3
                        else:
                            raise e
                    
                    # Verificación del archivo final
                    if not os.path.exists(final_path):
                        # Buscar archivos alternativos (ej. si no se pudo unir y quedó .mkv o algo así)
                        files = [f for f in os.listdir(temp_dir) if f.startswith(filename_base)]
                        if files:
                            # Preferir el más grande que no sea .part
                            files = [f for f in files if not f.endswith('.part')]
                            if files:
                                final_path = os.path.join(temp_dir, sorted(files, key=lambda x: os.path.getsize(os.path.join(temp_dir, x)), reverse=True)[0])
                            else:
                                raise Exception("Descarga incompleta")
                        else:
                            raise Exception("Archivo no encontrado tras la descarga.")
                    
                    # Verificación robusta del archivo resultante
                    if not os.path.exists(final_path):
                        # Buscar cualquier archivo que empiece con el prefijo (por si cambió la extensión)
                        possible_files = [f for f in os.listdir(temp_dir) if f.startswith(filename_base)]
                        if possible_files:
                            final_path = os.path.join(temp_dir, possible_files[0])
                        else:
                            raise Exception("Descarga completada pero no se encontró el archivo final.")


                    # Enviar el archivo
                    with open(final_path, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-Type', 'video/mp4')
                        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                        self.send_header('Content-Length', str(os.path.getsize(final_path)))
                        self.end_headers()
                        
                        # Streaming para evitar cargar archivos gigantes en RAM
                        while True:
                            chunk = f.read(8192)
                            if not chunk: break
                            self.wfile.write(chunk)
                        
                        logger.info(f"📤 Video enviado (HQ): {filename}")
                    return

                except Exception as e:
                    logger.error(f"❌ Error en descarga CLI: {str(e)}")
                    self.send_error(500, f"Error en descarga: {str(e)}")
                finally:
                    # Limpieza
                    files = [f for f in os.listdir(temp_dir) if f.startswith(filename_base)]
                    for f in files:
                        try: os.remove(os.path.join(temp_dir, f))
                        except: pass


            else:
                # Lógica legacy para otros sitios (proxy directo usando requests)
                logger.info(f"Descarga proxy estándar para: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                r = requests.get(url, stream=True, headers=headers, timeout=30)
                
                self.send_response(200)
                self.send_header('Content-Type', r.headers.get('Content-Type', 'video/mp4'))
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                if 'Content-Length' in r.headers:
                    self.send_header('Content-Length', r.headers['Content-Length'])
                self.end_headers()
                
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        self.wfile.write(chunk)

        except Exception as e:
            logger.error(f"Error general en descarga: {str(e)}")
            if not self.wfile.closed:
                self.send_error(500, f"Error: {str(e)}")

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
        """Sirve archivos estáticos con headers apropiados y protección de Path Traversal"""
        try:
            # Decodificar URL (ej. %20 -> espacio)
            filename = unquote(filename)

            # Protección estricta: No permitir navegación hacia arriba
            if '..' in filename:
                logger.warning(f"⛔ Intento de Path Traversal bloqueado (..): {filename}")
                self.send_error(403)
                return

            # Protección contra Path Traversal (Resolución)
            safe_base = os.path.realpath(os.getcwd())
            
            # Evitar rutas absolutas que ignoren safe_base en os.path.join
            if os.path.isabs(filename):
                 logger.warning(f"⛔ Intento de Path Traversal bloqueado (ruta absoluta): {filename}")
                 self.send_error(403)
                 return

            requested_path = os.path.realpath(os.path.join(safe_base, filename))
            
            # Verificación robusta usando commonpath para evitar errores de prefijo
            try:
                common = os.path.commonpath([safe_base, requested_path])
            except ValueError:
                logger.warning(f"⛔ Intento de Path Traversal bloqueado (drive mismatch): {filename}")
                self.send_error(403)
                return

            if common != safe_base:
                logger.warning(f"⛔ Intento de Path Traversal bloqueado (scope/commonpath): {filename}")
                self.send_error(403, "Forbidden")
                return

            if not os.path.exists(requested_path):
                logger.warning(f"Archivo no encontrado: {filename}")
                self.send_error(404)
                return
            
            if not os.path.isfile(requested_path):
                 self.send_error(403)
                 return

            with open(requested_path, 'rb') as f:
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
                return

            # Validación básica de protocolo
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                self.send_json_response(
                    {'success': False, 'error': 'Protocolo no válido'}, 400)
                return

            # Validar URL según plataforma
            if any(domain in url for domain in ['instagram.com', 'cdninstagram.com', 'linkedin.com', 'x.com', 'twitter.com', 'tiktok.com', 'facebook.com', 'fb.watch', 'youtube.com', 'youtu.be', 'm.youtube.com', 'twitch.tv', 'twitch.com', 'pinterest.com', 'pin.it']):
                self.send_json_response({
                    'success': True,
                    'url': url,
                    'message': 'URL válida'
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': 'Enlace no reconocido. Verifica que sea de una plataforma soportada (Instagram, TikTok, YouTube, Pinterest, etc.).'
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
            
            # Validación básica de protocolo SSFR
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                 self.send_json_response({'success': False, 'error': 'URL inválida (protocolo)'}, 400)
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
            if 'instagram.com' in url or 'cdninstagram.com' in url:
                extractor = InstagramExtractor()
                platform = 'instagram'
            elif 'twitch.tv' in url or 'twitch.com' in url:
                extractor = TwitchExtractor()
                platform = 'twitch'
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
            elif 'pinterest.com' in url or 'pin.it' in url:
                extractor = PinterestExtractor()
                platform = 'pinterest'
            else:
                return {
                    'success': False,
                    'error': 'Plataforma no soportada. Verifica que el enlace sea correcto.'
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
            
            # CORS policy reflection
            origin = self.headers.get('Origin', '*')
            self.send_header('Access-Control-Allow-Origin', origin)
            
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
        
        # CORS policy reflection
        origin = self.headers.get('Origin', '*')
        self.send_header('Access-Control-Allow-Origin', origin)
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server():
    """Inicia el servidor con configuración optimizada"""
    try:
        # Configuración del servidor
        host = '0.0.0.0'  # Escucha en todas las interfaces
        port = int(os.environ.get('PORT', 8000))  # Puerto dinámico para Railway/Heroku

        server = ThreadedHTTPServer((host, port), VideoDownloaderHandler)
        server.timeout = 60

        logger.info("=" * 60)
        logger.info("Video Downloader Server - High Quality Fix")
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

    try:
        from twitch_extractor import TwitchExtractor
        print("Twitch extractor: OK")
    except Exception as e:
        print(f"Twitch extractor error: {e}")

    try:
        from pinterest_extractor import PinterestExtractor
        print("Pinterest extractor: OK")
    except Exception as e:
        print(f"Pinterest extractor error: {e}")

    print()
    run_server()
