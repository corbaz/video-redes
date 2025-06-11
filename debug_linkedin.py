#!/usr/bin/env python3
"""
Script de debugging para LinkedIn extractor
"""

from linkedin_extractor import LinkedInExtractor
import json


def test_linkedin_extractor():
    """Prueba el extractor de LinkedIn con respuesta simulada"""
    print("🔍 Testing LinkedIn Extractor Response Structure...")

    # Simular respuesta exitosa
    mock_response = {
        "success": True,
        "data": {
            "videoUrl": "https://video.linkedin.com/sample-video.mp4"
        }
    }

    print(f"📊 Mock Response: {json.dumps(mock_response, indent=2)}")

    # Simular el frontend extrayendo la URL
    def extract_video_url(data):
        """Simula la función extractVideoUrl del frontend"""
        print(f"🔍 extractVideoUrl received: {json.dumps(data, indent=2)}")

        if data is None:
            print("❌ data is None")
            return None

        if data.get('videoUrl'):
            print(f"✅ Found videoUrl: {data['videoUrl']}")
            return data['videoUrl']
        if data.get('data') and data['data'].get('videoUrl'):
            print(f"✅ Found data.videoUrl: {data['data']['videoUrl']}")
            return data['data']['videoUrl']
        if data.get('url'):
            print(f"✅ Found url: {data['url']}")
            return data['url']
        if data.get('video_url'):
            print(f"✅ Found video_url: {data['video_url']}")
            return data['video_url']

        print("❌ No video URL found in any location")
        return None

    # Probar extracción desde mock_response.data
    video_url = extract_video_url(mock_response.get('data'))
    print(f"🎬 Extracted video URL: {video_url}")

    # Probar si también funciona con la respuesta completa
    video_url2 = extract_video_url(mock_response)
    print(f"🎬 Extracted from full response: {video_url2}")

    return mock_response


if __name__ == "__main__":
    test_linkedin_extractor()
