import requests
import re
import json

url = "https://www.linkedin.com/posts/codewithalamin_5-in-demand-ui-libraries-in-2025-ugcPost-7410643422371475456-BQ8L?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAG7i2kBJYOUUL_TjWJ0s_rD6_LBPtqzDEc"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Fetching {url}...")
try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    html = response.text
    
    # Save for manual inspection if needed
    with open("linkedin_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("HTML saved to linkedin_debug.html")

    # Regex tests
    print("\n--- Regex Tests ---")
    
    # Check for dms.licdn.com
    dms_matches = re.findall(r'(https://dms\.licdn\.com/[^"\s\\]+)', html)
    print(f"Found {len(dms_matches)} dms.licdn.com matches.")
    # for m in dms_matches[:5]:
    #     print(f" - {m}")
        
    # Look for data-native-document-config
    config_match = re.search(r'data-native-document-config="([^"]+)"', html)
    if config_match:
        print("\n✅ Found data-native-document-config")
        import html as html_lib
        json_str = html_lib.unescape(config_match.group(1))
        # print(f"JSON: {json_str[:100]}...")
        
        try:
            data = json.loads(json_str)
            doc_info = data.get('doc', {})
            manifest_url = doc_info.get('manifestUrl') or doc_info.get('url')
            
            if manifest_url:
                print(f"✅ Found Manifest URL: {manifest_url}")
                
                # Fetch the manifest to see if it has the PDF url
                print("Fetching manifest...")
                m_resp = requests.get(manifest_url, headers=headers, timeout=10)
                print(f"Manifest Status: {m_resp.status_code}")
                print(f"Manifest Content Start: {m_resp.text[:500]}")
                
                # Check formatting
                try:
                    m_json = m_resp.json()
                    # Look for distinct download URL
                    # usually it's not in the manifest, but let's check
                except:
                    pass
            else:
                print("❌ No manifestUrl in config")
        except Exception as ex:
            print(f"❌ JSON Parse Error: {ex}")

    else:
        print("❌ No data-native-document-config found")

except Exception as e:
    print(f"Error: {e}")
