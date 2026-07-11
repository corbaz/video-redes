"""Puente entre el servidor HTTP síncrono y un navegador Playwright real,
usado EXCLUSIVAMENTE por el administrador del sitio para refrescar la cookie
compartida de Instagram/Facebook sin exportar/pegar el archivo a mano.

Este mecanismo NUNCA se ofrece a visitantes públicos: la contraseña de un
tercero no puede pasar por este servidor bajo ninguna forma (el servidor
retransmite cada tecla al navegador real, así que verla es inevitable). Acá
la única persona logueándose es el propio administrador, con su propia
cuenta y su propio riesgo -- protegido por ADMIN_SECRET en server.py.

Diseño clave: la API síncrona de Playwright está confinada al hilo que la
inicia -- no es segura de llamar desde otros hilos. Por eso cada LoginSession
corre TODO su trabajo de Playwright en un único hilo propio (self._thread) y
expone métodos públicos (screenshot/replay_input) que empaquetan el pedido en
una cola y esperan el resultado, en vez de tocar los objetos de Playwright
directamente desde el hilo que atiende el request HTTP.

La cookie capturada se devuelve tal cual (lista de dicts estilo Playwright)
para que el llamador decida qué hacer con ella -- en este proyecto,
server.py la escribe directo en el archivo de cookies compartido.
"""

import queue
import shutil
import tempfile
import threading
import time
import uuid

from playwright.sync_api import sync_playwright


def cookies_to_netscape(cookies: list) -> str:
    """Convierte cookies estilo Playwright (dicts con name/value/domain/...)
    al formato Netscape que espera yt-dlp (--cookies archivo.txt)."""
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        domain = c.get('domain', '')
        include_subdomains = 'TRUE' if domain.startswith('.') else 'FALSE'
        expires = int(c.get('expires', -1) or -1)
        if expires <= 0:
            expires = int(time.time()) + 3600  # cookie de sesión: válida para este uso puntual
        secure = 'TRUE' if c.get('secure') else 'FALSE'
        lines.append('\t'.join([
            domain, include_subdomains, c.get('path', '/'), secure,
            str(expires), c.get('name', ''), c.get('value', ''),
        ]))
    return '\n'.join(lines) + '\n'

LOGIN_TARGET_URLS = {
    'instagram': 'https://www.instagram.com/accounts/login/',
    'facebook': 'https://www.facebook.com/login/',
}

# Selectores candidatos de los campos usuario/contraseña por plataforma, para
# autocompletar las credenciales del administrador. Instagram/Facebook sirven
# variantes del formulario según región/IP (a veces username/password, a veces
# email/pass), así que probamos varios. El envío (Enter) lo hace la persona a
# mano -- mantiene un humano en el lazo y reduce (no elimina) la detección.
LOGIN_FIELD_SELECTORS = {
    'instagram': {
        'user': ["input[name='username']", "input[name='email']"],
        'pass': ["input[name='password']", "input[name='pass']"],
    },
    'facebook': {
        'user': ["input[name='email']", "input[name='username']", "#email"],
        'pass': ["input[name='pass']", "input[name='password']", "#pass"],
    },
}

# Cookies que solo existen una vez el login fue exitoso -- señal confiable,
# a diferencia de intentar parsear el DOM de una pantalla de login que
# cambia seguido. Requerimos TODAS las de la lista para no capturar un set
# incompleto (yt-dlp necesita el juego completo para autenticar la descarga).
AUTH_COOKIE_NAMES = {
    'instagram': ['sessionid', 'ds_user_id'],
    'facebook': ['c_user', 'xs'],
}

# Tras detectar las cookies de auth, esperar a que Instagram/Facebook terminen
# de asentar todo el juego (evita capturar a mitad de la navegación).
_COOKIE_SETTLE_SECONDS = 2.5

# Evasiones básicas de fingerprinting (no garantizan evitar detección de
# Meta, en especial por reputación de IP de datacenter -- ver README).
_STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['es-AR', 'es', 'en'] });
window.chrome = window.chrome || { runtime: {} };
"""

IDLE_TIMEOUT_SECONDS = 120
MAX_SESSION_AGE_SECONDS = 600
_COMMAND_TIMEOUT_SECONDS = 10


class LoginSessionError(Exception):
    pass


class LoginSession:
    def __init__(self, platform: str, username: str = '', password: str = ''):
        if platform not in LOGIN_TARGET_URLS:
            raise LoginSessionError(f"Plataforma no soportada: {platform}")

        self.id = str(uuid.uuid4())
        self.platform = platform
        self._username = username
        self._password = password
        self.status = 'loading'  # loading | active | success | error | expired
        self.error = None
        self.cookies = None
        self.created_at = time.time()
        self.last_activity = time.time()
        self._auth_first_seen = None

        self._profile_dir = tempfile.mkdtemp(prefix='pw_login_')
        self._cmd_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # --- API pública, llamada desde hilos de request HTTP -----------------

    def screenshot(self) -> bytes:
        return self._dispatch('screenshot', {})

    def replay_input(self, event: dict):
        self._dispatch('input', event)
        self.touch()

    def touch(self):
        with self._state_lock:
            self.last_activity = time.time()

    def is_expired(self) -> bool:
        now = time.time()
        with self._state_lock:
            if now - self.created_at > MAX_SESSION_AGE_SECONDS:
                return True
            if now - self.last_activity > IDLE_TIMEOUT_SECONDS:
                return True
        return False

    def close(self):
        self._stop_event.set()
        self._thread.join(timeout=5)
        shutil.rmtree(self._profile_dir, ignore_errors=True)

    # --- Interno: todo lo de Playwright vive en este único hilo -----------

    def _dispatch(self, kind: str, payload: dict):
        result_holder = {'event': threading.Event(), 'result': None, 'error': None}
        self._cmd_queue.put((kind, payload, result_holder))
        if not result_holder['event'].wait(timeout=_COMMAND_TIMEOUT_SECONDS):
            raise LoginSessionError("Tiempo de espera agotado esperando al navegador")
        if result_holder['error']:
            raise result_holder['error']
        return result_holder['result']

    def _run(self):
        try:
            print(f"🌐 [login {self.platform}] lanzando Chromium (perfil {self._profile_dir})...")
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    self._profile_dir,
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                    ],
                    viewport={'width': 1280, 'height': 800},
                )
                context.add_init_script(_STEALTH_INIT_SCRIPT)
                page = context.pages[0] if context.pages else context.new_page()
                print(f"🌐 [login {self.platform}] navegando a la página de login...")
                page.goto(LOGIN_TARGET_URLS[self.platform], timeout=30000)
                try:
                    print(f"🌐 [login {self.platform}] cargó: url={page.url!r} title={page.title()!r}")
                except Exception:
                    pass
                self._autofill_credentials(page)
                self.status = 'active'
                print(f"🌐 [login {self.platform}] status=active, listo para stream/interacción")

                first_shot_logged = False
                while not self._stop_event.is_set():
                    self._check_login_cookie(context)
                    if self.status == 'success':
                        print(f"✅ [login {self.platform}] cookie de sesión detectada")
                        break
                    try:
                        kind, payload, result_holder = self._cmd_queue.get(timeout=0.3)
                    except queue.Empty:
                        continue
                    try:
                        result_holder['result'] = self._execute(kind, payload, page)
                        if kind == 'screenshot' and not first_shot_logged:
                            size = len(result_holder['result']) if result_holder['result'] else 0
                            print(f"📸 [login {self.platform}] primer screenshot: {size} bytes")
                            first_shot_logged = True
                    except Exception as e:
                        result_holder['error'] = e
                        print(f"⚠️ [login {self.platform}] error ejecutando {kind}: {e}")
                    finally:
                        result_holder['event'].set()

                context.close()
        except Exception as e:
            self.status = 'error'
            self.error = str(e)
            print(f"❌ [login {self.platform}] FALLO en _run: {type(e).__name__}: {e}")

    def _autofill_credentials(self, page):
        """Rellena usuario y contraseña del admin si vinieron por env.
        No envía el formulario: el Enter lo hace la persona a mano."""
        if not self._username or not self._password:
            return
        selectors = LOGIN_FIELD_SELECTORS.get(self.platform)
        if not selectors:
            return
        # Descartar banner de cookies si aparece (varía por región).
        try:
            page.click("text=/Allow all cookies|Permitir todas|Only allow essential/i", timeout=4000)
        except Exception:
            pass
        if not self._fill_first(page, selectors['user'], self._username):
            print("⚠️ No se encontró el campo de usuario para autocompletar.")
        if not self._fill_first(page, selectors['pass'], self._password):
            print("⚠️ No se encontró el campo de contraseña para autocompletar.")

    @staticmethod
    def _fill_first(page, candidate_selectors, value) -> bool:
        """Prueba cada selector candidato y rellena el primero que exista."""
        for selector in candidate_selectors:
            try:
                page.fill(selector, value, timeout=5000)
                return True
            except Exception:
                continue
        return False

    def _execute(self, kind: str, payload: dict, page):
        if kind == 'screenshot':
            return page.screenshot(type='jpeg', quality=60, timeout=5000)
        if kind == 'input':
            self._replay_on_page(page, payload)
            return None
        raise LoginSessionError(f"Comando desconocido: {kind}")

    def _replay_on_page(self, page, event: dict):
        etype = event.get('type')
        if etype == 'move':
            page.mouse.move(event['x'], event['y'])
        elif etype == 'click':
            page.mouse.click(event['x'], event['y'])
        elif etype == 'type':
            page.keyboard.type(event.get('text', ''))
        elif etype == 'key':
            page.keyboard.press(event.get('key', ''))
        elif etype == 'scroll':
            page.mouse.wheel(0, event.get('deltaY', 0))

    def _check_login_cookie(self, context):
        required = AUTH_COOKIE_NAMES[self.platform]
        names = {c['name'] for c in context.cookies()}
        if not all(n in names for n in required):
            # Todavía no está el juego completo de cookies de auth.
            self._auth_first_seen = None
            return
        now = time.time()
        if self._auth_first_seen is None:
            # Primera vez que vemos el set completo: esperar a que se asiente.
            self._auth_first_seen = now
            return
        if now - self._auth_first_seen < _COOKIE_SETTLE_SECONDS:
            return
        # Ya asentado: capturar el juego completo y marcar éxito.
        self.cookies = context.cookies()
        self.status = 'success'
