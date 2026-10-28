"""Combina todos los archivos de cookies de la carpeta cookies/ en uno solo.

La extensión "Get cookies.txt LOCALLY" exporta un archivo por dominio
(www.instagram.com_cookies.txt, www.facebook.com_cookies.txt, ...). En vez de
obligar a renombrar/pegar a mano, juntamos TODOS los .txt de la carpeta en un
único archivo Netscape que yt-dlp consume con --cookies.

Reglas:
- Se ignora el propio combinado (all_cookies.txt) como fuente.
- Se deduplica por (dominio, nombre); ante duplicados gana el archivo más
  nuevo (por fecha de modificación), así una cookie recién exportada pisa a la
  vieja.
- Un export en formato "Header String" (todo en una línea: a=1; b=2) se
  convierte a Netscape con el dominio del nombre del archivo
  (www.linkedin.com_cookies.txt -> .linkedin.com). Las líneas que no se pueden
  convertir se descartan: yt-dlp no las entiende y las volcaría al log.
"""

import os
import glob
import re

COMBINED_NAME = 'all_cookies.txt'
_EXPORT_SUFFIX = '_cookies.txt'
# Nombre que pone la extensión: www.linkedin.com_cookies.txt. Sin barras ni
# "..", así un upload del panel admin no puede escribir fuera de cookies/.
_EXPORT_NAME_RE = re.compile(r'^[a-z0-9-]+(\.[a-z0-9-]+)+_cookies\.txt$')


def _file_domain(path):
    """'.linkedin.com' para www.linkedin.com_cookies.txt; None si no aplica."""
    name = os.path.basename(path)
    if not name.endswith(_EXPORT_SUFFIX):
        return None
    host = name[:-len(_EXPORT_SUFFIX)]
    if host.startswith('www.'):
        host = host[4:]
    return '.' + host if '.' in host else None


def _netscape_lines(line, domain):
    """Las líneas Netscape que aporta una línea de un archivo de cookies."""
    if len(line.split('\t')) >= 7:
        return [line]
    if not domain:
        return []
    out = []
    for pair in line.split(';'):
        name, sep, value = pair.strip().partition('=')
        if sep and name:
            out.append('\t'.join([domain, 'TRUE', '/', 'TRUE', '0', name, value]))
    return out


def _cookies_dir():
    env_file = os.environ.get('INSTAGRAM_COOKIES_FILE')
    if env_file:
        return os.path.dirname(os.path.abspath(env_file))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'cookies'))


def save_cookie_file(name, content):
    """Guarda un export de cookies en la carpeta con su propio nombre.

    Lanza ValueError si el nombre no es el de un export de la extensión o si
    el contenido está vacío. Devuelve la ruta guardada.
    """
    name = (name or '').strip().lower()
    if not _EXPORT_NAME_RE.match(name):
        raise ValueError(
            f"Nombre inválido: usá el que pone la extensión (ej. www.linkedin.com{_EXPORT_SUFFIX})")
    if not (content or '').strip():
        raise ValueError(f"El archivo {name} está vacío")

    directory = _cookies_dir()
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    return path


def combined_cookies_file():
    """Devuelve la ruta de un archivo de cookies combinado, o None si no hay
    ningún .txt en la carpeta."""
    directory = _cookies_dir()
    if not os.path.isdir(directory):
        return None

    sources = [
        p for p in glob.glob(os.path.join(directory, '*.txt'))
        if os.path.basename(p) != COMBINED_NAME
    ]
    if not sources:
        return None

    # Más nuevos primero: sus cookies ganan ante duplicados.
    sources.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    lines = ['# Netscape HTTP Cookie File', '# Combinado por cookies_util.py', '']
    seen = set()
    for path in sources:
        domain = _file_domain(path)
        try:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                for raw in fh:
                    s = raw.rstrip('\r\n')
                    if not s.strip() or s.lstrip().startswith('#'):
                        continue
                    for cookie in _netscape_lines(s, domain):
                        parts = cookie.split('\t')
                        key = (parts[0], parts[5])
                        if key in seen:
                            continue
                        seen.add(key)
                        lines.append(cookie)
        except Exception:
            continue

    out_path = os.path.join(directory, COMBINED_NAME)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out_path
