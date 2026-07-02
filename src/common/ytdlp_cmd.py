import os
import sys
import shutil


def resolve_ytdlp() -> list:
    """Locate yt-dlp reliably: venv Scripts dir first, then PATH,
    then the installed Python module as last resort."""
    exe_dir = os.path.dirname(sys.executable)
    for name in ('yt-dlp.exe', 'yt-dlp'):
        candidate = os.path.join(exe_dir, name)
        if os.path.isfile(candidate):
            return [candidate]
    if shutil.which('yt-dlp'):
        return ['yt-dlp']
    return [sys.executable, '-m', 'yt_dlp']


YTDLP_CMD = resolve_ytdlp()
