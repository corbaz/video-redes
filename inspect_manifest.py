import requests
import json

url = "https://media.licdn.com/dms/document/pl/v2/D561FAQERXOYKq9OJIQ/feedshare-document-master-manifest/B56ZtfkhU1JgBc-/0/1766834972241?e=2147483647&v=beta&t=enzoloSo-RK5p5RZxScrGH57bk4xP7LkhyZIuqUK6ks"

try:
    print("Fetching manifest...")
    r = requests.get(url, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    
    try:
        data = r.json()
        print("JSON Keys:", list(data.keys()))
        if 'assets' in data:
            print("Assets count:", len(data['assets']))
            # Check first asset logic
            print("First asset:", data['assets'][0])
        if 'transcribedDocumentUrl' in data:
            print(f"Transcribed Doc URL: {data['transcribedDocumentUrl']}")
        if 'asset' in data:
             print(f"Asset: {data.get('asset')}")
    except Exception as e:
        print(f"Not JSON: {e}")
        print("First 100 bytes:", r.content[:100])
except Exception as e:
    print(f"Error: {e}")
