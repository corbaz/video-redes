#!/usr/bin/env python3
"""
Test rápido con simulación de LinkedIn
"""

from linkedin_extractor import LinkedInExtractor
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


def test_linkedin_simulation():
    """Test con URL de simulación para verificar estructura"""
    print("🔍 Testing LinkedIn Simulation...")

    extractor = LinkedInExtractor()

    # Usar URL de simulación
    test_url = "https://www.linkedin.com/posts/success-simulation"

    result = extractor.extract_info(test_url)

    print(f"📊 Result: {result}")

    if result.get("success"):
        data = result.get("data")
        if data and "videoUrl" in data:
            print("✅ SUCCESS: Correct structure with data.videoUrl")
            print(f"🎬 Video URL: {data['videoUrl']}")
        else:
            print("❌ WRONG: Missing data.videoUrl")
    else:
        print(f"❌ FAILED: {result.get('error')}")


if __name__ == "__main__":
    test_linkedin_simulation()
