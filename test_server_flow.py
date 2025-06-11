#!/usr/bin/env python3
"""
Test completo del flujo servidor -> extractor -> respuesta
"""

from linkedin_extractor import LinkedInExtractor
import json


def test_server_flow():
    """Simula el flujo completo del servidor"""
    print("🔍 Testing Server Flow...")

    # Simular _handle_extract del servidor
    def simulate_handle_extract(url):
        print(f"📡 Server handling extract for: {url}")

        # Detectar plataforma
        if 'linkedin.com' in url:
            print("🔗 Detected LinkedIn URL")
            extractor = LinkedInExtractor()
            result = extractor.extract_info(url)
        else:
            print("📷 Detected Instagram URL")
            result = {"success": False,
                      "error": "Instagram not implemented in test"}

        print(f"📊 Extractor result: {json.dumps(result, indent=2)}")

        # Simular _send_json del servidor
        status = 200 if result.get("success") else 400
        print(f"📡 Server sending JSON with status {status}")

        return result
      # Probar URLs
    test_urls = [
        "https://www.linkedin.com/posts/test-post",
        "https://www.linkedin.com/posts/success-simulation",  # Simular éxito
        "https://www.instagram.com/p/test-post"
    ]

    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"🧪 Testing URL: {url}")
        result = simulate_handle_extract(url)

        # Simular frontend recibiendo la respuesta
        print(f"\n🌐 Frontend receives:")
        print(f"   extractResponse = {json.dumps(result, indent=2)}")
        print(f"   extractResponse.success = {result.get('success')}")
        print(f"   extractResponse.data = {result.get('data')}")

        if result.get("success"):
            data = result.get("data")
            print(f"   showSuccess(data) called with: {data}")
            if data is None:
                print("   ❌ ERROR: data is None!")
            elif "videoUrl" in data:
                print(f"   ✅ SUCCESS: videoUrl = {data['videoUrl']}")
            else:
                print("   ❌ ERROR: data missing videoUrl!")
        else:
            print(f"   ❌ FAILED: {result.get('error')}")


if __name__ == "__main__":
    test_server_flow()
