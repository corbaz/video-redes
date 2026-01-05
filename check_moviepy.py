from moviepy.config import get_setting
import os
print(f"FFMPEG_BINARY env: {os.environ.get('FFMPEG_BINARY')}")
try:
    print(f"MoviePy Detected Binary: {get_setting('FFMPEG_BINARY')}")
except Exception as e:
    print(f"Error getting setting: {e}")
