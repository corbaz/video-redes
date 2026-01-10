
import requests
import re
import json
import sys

# Flush output
sys.stdout.reconfigure(encoding='utf-8')

url = "https://pin.it/4uPy0e10B"
print(f"Fetching {url}")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}
session = requests.Session()
response = session.get(url, headers=headers, allow_redirects=True)
html = response.text
print(f"Final URL: {response.url}")
print(f"Status Code: {response.status_code}")

# 1. Check for MP4 (Regex)
print("\n--- MP4 Regex ---")
mp4_matches = re.findall(r'(https?://[^"\'\s]+\.pinimg\.com/[^"\'\s]+\.mp4)', html)
print(f"MP4 Matches: {list(set(mp4_matches))}")

# 2. Check for HLS (m3u8) - sometimes videos are streams
print("\n--- M3U8 Regex ---")
m3u8_matches = re.findall(r'(https?://[^"\'\s]+\.m3u8)', html)
print(f"M3U8 Matches: {list(set(m3u8_matches))}")

# 3. Check for Images (Regex)
print("\n--- Image Regex ---")
img_matches = re.findall(r'(https?://i\.pinimg\.com/originals/[^"\'\s]+\.(?:jpg|png|jpeg|webp))', html)
print(f"Originals: {list(set(img_matches))}")

# 4. Check PWS_DATA
print("\n--- PWS_DATA ---")
json_match = re.search(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if json_match:
    print("PWS_DATA block found.")
    try:
        data = json.loads(json_match.group(1))
        # Navigate to find video data
        # props -> initialReduxState -> pins -> [ID] -> videos
        if 'props' in data and 'initialReduxState' in data['props'] and 'pins' in data['props']['initialReduxState']:
             pins = data['props']['initialReduxState']['pins']
             for pid, pdata in pins.items():
                 print(f"Pin ID: {pid}")
                 if 'videos' in pdata and pdata['videos']:
                     print(f"Videos data found: {json.dumps(pdata['videos'], indent=2)}")
                 else:
                     print("No 'videos' key in pin data")
                 
                 if 'story_pin_data' in pdata and pdata['story_pin_data']:
                      print("Story Pin Data found (might contain video pages)")
                      # pages -> [blocks] -> video
    except Exception as e:
        print(f"JSON Error: {e}")
else:
    print("PWS_DATA not found")

# 5. Check if we hit a login wall or captcha
if "login" in response.url or "Log in" in html:
    print("\n⚠️  Redirected to Login / Login detected in HTML")
