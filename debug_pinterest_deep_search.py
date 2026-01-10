
import requests
import re
import json
import sys

# Flush output
sys.stdout.reconfigure(encoding='utf-8')

url = "https://pin.it/3Yl66Pcgj"
print(f"Fetching {url}")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
session = requests.Session()
response = session.get(url, headers=headers, allow_redirects=True)
html = response.text

print(f"Final URL: {response.url}")

def recursive_find_images(data, found=None):
    if found is None:
        found = []
    
    if isinstance(data, dict):
        for k, v in data.items():
            if k == 'images' and isinstance(v, dict):
                # Common pinterest image structure
                if 'orig' in v:
                    found.append(v['orig']['url'])
                elif '736x' in v:
                    found.append(v['736x']['url'])
                elif '474x' in v:
                    found.append(v['474x']['url'])
            # Check for direct url keys that look like pinterest images
            if k == 'url' and isinstance(v, str) and 'i.pinimg.com' in v:
                found.append(v)
            
            recursive_find_images(v, found)
            
    elif isinstance(data, list):
        for item in data:
            recursive_find_images(item, found)
            
    return found

# 1. Try PWS_DATA
print("\n--- Searching PWS_DATA ---")
json_match = re.search(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if json_match:
    try:
        data = json.loads(json_match.group(1))
        images = recursive_find_images(data)
        print(f"Recursive JSON found: {list(set(images))}")
    except Exception as e:
        print(f"JSON error: {e}")
else:
    print("No PWS_DATA found")

# 2. Try generic regex again (Verify)
print("\n--- Regex Verification ---")
regex_imgs = re.findall(r'(https?://i\.pinimg\.com/[^"\'\s]+\.(?:jpg|png|jpeg|webp))', html)
print(f"Regex found: {len(regex_imgs)} candidates")
if regex_imgs:
    print(f"Top 3: {regex_imgs[:3]}")

