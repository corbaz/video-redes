
import requests
import re
import json
import sys

# Flush output immediately
sys.stdout.reconfigure(encoding='utf-8')

url = "https://pin.it/6fDctLug0"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Fetching {url}...")
session = requests.Session()
response = session.get(url, headers=headers, allow_redirects=True)
html = response.text
print(f"Page size: {len(html)}")

json_data_match = re.search(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if json_data_match:
    print("Found script tag.")
    try:
        data = json.loads(json_data_match.group(1))
        print(f"Top keys: {list(data.keys())}")
        
        if 'props' in data:
            print("Found 'props'")
            props = data['props']
            if 'initialReduxState' in props:
                print("Found 'initialReduxState'")
                state = props['initialReduxState']
                print(f"State keys: {list(state.keys())}")
                
                if 'pins' in state:
                    pins = state['pins']
                    print(f"Pins found: {len(pins)}")
                    for pin_id, pin_data in pins.items():
                        print(f"--- Pin ID: {pin_id} ---")
                        # Basic Image
                        if 'images' in pin_data:
                            print(f"Images variant keys: {list(pin_data['images'].keys())}")
                            if 'orig' in pin_data['images']:
                                print(f"ORIG IMAGE: {pin_data['images']['orig']['url']}")
                        
                        # Videos or Video Data
                        if pin_data.get('videos'):
                            print("VIDEOS key found but null?" if not pin_data['videos'] else f"VIDEOS data: {pin_data['videos']}")
                        
                        # Check specific video fields
                        print(f"Video Status: {pin_data.get('video_status')}")
                        print(f"Is Video: {pin_data.get('is_video')}")
                        
                        # Sometimes videos are in 'story_pin_data'
                        if pin_data.get('story_pin_data'):
                            print("Found STORY PIN DATA")

                else:
                    print("'pins' key not found in state")
            else:
                 print("'initialReduxState' not found in props")
        else:
            print("'props' not found in data")

    except Exception as e:
        print(f"Error parsing JSON: {e}")
else:
    print("PWS_DATA script tag not found via Regex")
