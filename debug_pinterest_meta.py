
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

og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
print(f"OG Image: {og_image.group(1) if og_image else 'Not found'}")

og_image_name = re.search(r'<meta name="og:image" content="([^"]+)"', html)
print(f"OG Image (name): {og_image_name.group(1) if og_image_name else 'Not found'}")

# Look for any meta content that looks like an image
meta_imgs = re.findall(r'<meta[^>]+content="([^"]*pinimg[^"]*)"', html)
print(f"Meta content images: {meta_imgs}")
