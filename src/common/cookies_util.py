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
"""

import os
import glob

COMBINED_NAME = 'all_cookies.txt'


def _cookies_dir():
    env_file = os.environ.get('INSTAGRAM_COOKIES_FILE')
    if env_file:
        return os.path.dirname(os.path.abspath(env_file))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'cookies'))


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
        try:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                for raw in fh:
                    s = raw.rstrip('\r\n')
                    if not s.strip() or s.lstrip().startswith('#'):
                        continue
                    parts = s.split('\t')
                    key = (parts[0], parts[5]) if len(parts) >= 7 else s
                    if key in seen:
                        continue
                    seen.add(key)
                    lines.append(s)
        except Exception:
            continue

    out_path = os.path.join(directory, COMBINED_NAME)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out_path
