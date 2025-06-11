#!/usr/bin/env python3
"""
Test manual del servidor web
"""

import requests
import json


def test_api():
    """Prueba la API del servidor manualmente"""
    base_url = "http://localhost:8000"

    print("🔍 Testing API manually...")

    # URLs de prueba
    test_cases = [
        {
            "name": "LinkedIn Success Simulation",
            "url": "https://www.linkedin.com/posts/success-simulation"
        },
        {
            "name": "LinkedIn Error",
            "url": "https://www.linkedin.com/posts/test-post"
        },
        {
            "name": "Invalid URL",
            "url": "https://www.youtube.com/watch?v=invalid"
        }
    ]

    for case in test_cases:
        print(f"\n{'='*50}")
        print(f"🧪 Testing: {case['name']}")
        print(f"📎 URL: {case['url']}")

        try:
            # Test validate
            print("📡 Testing /api/validate...")
            validate_response = requests.post(f"{base_url}/api/validate",
                                              json={"url": case['url']},
                                              timeout=5)
            print(f"   Status: {validate_response.status_code}")
            validate_data = validate_response.json()
            print(f"   Response: {json.dumps(validate_data, indent=2)}")

            if validate_data.get("success"):
                # Test extract
                print("📡 Testing /api/extract...")
                extract_response = requests.post(f"{base_url}/api/extract",
                                                 json={
                                                     "url": validate_data["url"]},
                                                 timeout=15)
                print(f"   Status: {extract_response.status_code}")
                extract_data = extract_response.json()
                print(f"   Response: {json.dumps(extract_data, indent=2)}")

                # Simular frontend
                print("🌐 Simulating frontend logic...")
                if extract_data.get("success"):
                    data = extract_data.get("data")
                    if data:
                        print(f"   ✅ showSuccess would be called with: {data}")
                        if "videoUrl" in data:
                            print(f"   🎬 Video URL: {data['videoUrl']}")
                        else:
                            print("   ❌ Missing videoUrl in data")
                    else:
                        print("   ❌ data is None/undefined - ERROR detected!")
                else:
                    print(f"   ❌ Extract failed: {extract_data.get('error')}")
            else:
                print(f"   ❌ Validate failed: {validate_data.get('error')}")

        except requests.exceptions.ConnectionError:
            print("   ❌ Server not running - start server first")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    test_api()
