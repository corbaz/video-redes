
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

print("\n--- Searching for LD+JSON ---")
ld_json_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)

for i, match in enumerate(ld_json_matches):
    print(f"\nMatch #{i+1}:")
    try:
        data = json.loads(match)
        print(json.dumps(data, indent=2)[:500] + "...")
        if '@type' in data and data['@type'] == 'SocialMediaPosting':
            print("FOUND SocialMediaPosting!")
            if 'image' in data:
                print(f"Image: {data['image']}")
            if 'video' in data:
                print(f"Video: {data['video']}")
    except Exception as e:
        print(f"JSON Parse Error: {e}")
