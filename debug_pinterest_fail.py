
import requests
import re
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

# Search for Images
print("\n--- Searching for Images ---")
# Pinimg usually: i.pinimg.com/originals/..., i.pinimg.com/236x/...
img_matches = re.findall(r'(https?://i\.pinimg\.com/[^"\'\s]+\.(?:jpg|png|jpeg|webp))', html)
unique_img = list(set(img_matches))

# Filter for originals
originals = [u for u in unique_img if '/originals/' in u]
print(f"Originals Found: {originals}")

if not originals:
    print("No originals found, checking others...")
    print(f"Total images found: {len(unique_img)}")
    if len(unique_img) > 0:
        print(f"Sample: {unique_img[:5]}")

# Dump a small part of HTML to check image tags if regex fails
if len(unique_img) == 0:
    print("\n--- HTML Dump (Partial) ---")
    print(html[:2000])
