
import requests
import re
import sys

# Flush output
sys.stdout.reconfigure(encoding='utf-8')

url = "https://pin.it/6fDctLug0"
print(f"Fetching {url}")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
session = requests.Session()
response = session.get(url, headers=headers, allow_redirects=True)
html = response.text

# 1. Search for video files (v.pinimg.com or similar ending in .mp4)
print("\n--- Searching for MP4 ---")
mp4_matches = re.findall(r'(https?://[^"\'\s]+\.pinimg\.com/[^"\'\s]+\.mp4)', html)
unique_mp4 = list(set(mp4_matches))
print(f"MP4 Found: {unique_mp4}")

# 2. Search for Images
print("\n--- Searching for Images ---")
# Pinimg usually: i.pinimg.com/originals/..., i.pinimg.com/236x/...
img_matches = re.findall(r'(https?://i\.pinimg\.com/[^"\'\s]+)', html)
unique_img = list(set(img_matches))

# Filter for originals
originals = [u for u in unique_img if '/originals/' in u]
print(f"Originals Found: {originals}")

if not originals:
    print("No originals found, checking others...")
    print(f"Total images found: {len(unique_img)}")
    if len(unique_img) > 0:
        print(f"Sample: {unique_img[:3]}")

