#!/usr/bin/env python3
"""
Test directo del extractor de LinkedIn real
"""

from linkedin_extractor import LinkedInExtractor
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


def test_real_linkedin_extractor():
    """Prueba el extractor de LinkedIn real con una URL de LinkedIn válida"""
    print("🔍 Testing REAL LinkedIn Extractor...")

    # URL real de LinkedIn para probar
    test_url = "https://www.linkedin.com/posts/midudev_esta-web-es-una-mina-de-oro-para-programadores-activity-7337115357532291072-Nacs"

    extractor = LinkedInExtractor()

    print(f"📎 Testing URL: {test_url}")

    try:
        result = extractor.extract_info(test_url)
        print(f"📊 Result type: {type(result)}")
        print(
            f"📊 Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        print(f"📊 Full result:")

        import json
        print(json.dumps(result, indent=2, default=str))

        # Verificar estructura esperada
        if result.get("success"):
            data = result.get("data")
            if data and "videoUrl" in data:
                print("✅ CORRECT: Found success=True and data.videoUrl")
                print(f"🎬 Video URL: {data['videoUrl'][:100]}...")
            else:
                print("❌ WRONG: success=True but missing data.videoUrl")
                print(f"   data = {data}")
        else:
            print(f"❌ FAILED: {result.get('error')}")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_linkedin_extractor()
