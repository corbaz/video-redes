
import requests
import re
import json
from yt_dlp import YoutubeDL

url = "https://pin.it/6fDctLug0"

print(f"Testing URL: {url}")

# 1. Test yt-dlp
print("\n--- Testing yt-dlp ---")
try:
    with YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        print("yt-dlp success!")
        print(f"Type: {info.get('_type')}")
        print(f"Formats: {len(info.get('formats', []))}")
except Exception as e:
    print(f"yt-dlp failed: {e}")

# 2. Test manual extraction
print("\n--- Testing manual extraction ---")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    session = requests.Session()
    response = session.get(url, headers=headers, allow_redirects=True, timeout=10)
    print(f"Final URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    
    html = response.text
    
    # Check meta tags
    og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    print(f"OG Image: {og_image.group(1) if og_image else 'Not found'}")
    
    og_video = re.search(r'<meta property="og:video" content="([^"]+)"', html)
    print(f"OG Video: {og_video.group(1) if og_video else 'Not found'}")
    
    # Check for __PWS_DATA__ or similar JSON data
    json_data_match = re.search(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if json_data_match:
        print("Found __PWS_DATA__")
        try:
            data = json.loads(json_data_match.group(1))
            # navigate data to find media
            print("JSON parsed successfully")
        except:
            print("JSON parse failed")
    else:
        print("No __PWS_DATA__ found")

except Exception as e:
    print(f"Manual failed: {e}")
