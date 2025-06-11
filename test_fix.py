#!/usr/bin/env python3
"""
Test del fix para LinkedIn - simula la respuesta real que está devolviendo
"""


def test_linkedin_response_fix():
    """Simula la respuesta real de LinkedIn y el procesamiento del frontend"""

    # Esta es la respuesta REAL que LinkedIn está devolviendo (según el log)
    linkedin_real_response = {
        "success": True,
        "video_url": "https://dms.licdn.com/playlist/vid/v2/D4D10AQGaJGOe-dcDDA/mp4-720p-30fp-crf28/B4DZdKrXlvHMBE-/0/1749304615701",
        "title": "¡Esta web es una mina de oro para programadores!\n+1500 plantillas HTML… | Miguel Angel Durán García | 11 comments",
        "html": ""
        # NOTA: No hay campo "data"
    }

    # Esta es la respuesta que Instagram está devolviendo (funciona)
    instagram_response = {
        "success": True,
        "data": {
            "title": "Video by melisaescobart",
            "uploader": "Melisa Escobar | Vender con IA 🤖",
            "video_formats": [
                {
                    "url": "https://scontent-eze1-1.cdninstagram.com/o1/v/t16/f2/m86/sample.mp4"
                }
            ]
        }
    }

    print("🧪 TESTING LINKEDIN RESPONSE FIX")
    print("=" * 50)

    def simulate_new_frontend_logic(extractResponse, platform):
        """Simula la nueva lógica del frontend"""
        print(f"\n📱 Testing {platform.upper()} response...")
        print(f"extractResponse = {extractResponse}")

        if extractResponse.get("success"):
            data = extractResponse.get("data")
            print(f"5. Initial data from extractResponse.data: {data}")

            # Si no hay 'data', usar toda la respuesta (caso LinkedIn actual)
            if not data:
                print("6. No extractResponse.data found, using full response")
                data = extractResponse

            print(f"7. Final data to pass to showSuccess: {data}")

            # Simular showSuccess
            return simulate_show_success(data, platform)
        else:
            print(f"❌ {platform}: Extract failed")
            return False

    def simulate_show_success(data, platform):
        """Simula showSuccess con la nueva lógica extractVideoUrl"""
        print(f"🎯 showSuccess() called for {platform}")

        if not data:
            print("❌ ERROR: showSuccess received undefined/null data")
            return False

        # Simular extractVideoUrl mejorada
        video_url = extract_video_url_improved(data)
        print(f"🔗 {platform}: videoUrl extracted = {video_url}")

        if video_url:
            print(f"✅ SUCCESS: {platform} video URL found!")
            return True
        else:
            print(f"❌ ERROR: No video URL found for {platform}")
            return False

    def extract_video_url_improved(data):
        """Simula la función extractVideoUrl mejorada"""
        print(f"🔍 extractVideoUrl: searching in data: {type(data)}")

        # Estructura estándar: data.videoUrl
        if data.get('videoUrl'):
            print(f"✅ Found data.videoUrl: {data['videoUrl']}")
            return data['videoUrl']

        # Estructura anidada: data.data.videoUrl
        if data.get('data') and data['data'].get('videoUrl'):
            print(f"✅ Found data.data.videoUrl: {data['data']['videoUrl']}")
            return data['data']['videoUrl']

        # LinkedIn directo: data.video_url (respuesta actual de LinkedIn)
        if data.get('video_url'):
            print(f"✅ Found data.video_url: {data['video_url']}")
            return data['video_url']

        # Alternativas
        if data.get('url'):
            print(f"✅ Found data.url: {data['url']}")
            return data['url']

        # Buscar en arrays de formatos
        if data.get('video_formats') and len(data['video_formats']) > 0:
            format_url = data['video_formats'][0].get('url')
            print(f"✅ Found data.video_formats[0].url: {format_url}")
            return format_url

        if data.get('data') and data['data'].get('video_formats') and len(data['data']['video_formats']) > 0:
            format_url = data['data']['video_formats'][0].get('url')
            print(f"✅ Found data.data.video_formats[0].url: {format_url}")
            return format_url

        print("❌ No video URL found in any location")
        return None

    # Probar ambas respuestas
    linkedin_result = simulate_new_frontend_logic(
        linkedin_real_response, "linkedin")
    instagram_result = simulate_new_frontend_logic(
        instagram_response, "instagram")

    print(f"\n{'='*50}")
    print("🏁 RESULTS:")
    print(f"LinkedIn: {'✅ FIXED' if linkedin_result else '❌ STILL BROKEN'}")
    print(f"Instagram: {'✅ WORKS' if instagram_result else '❌ BROKEN'}")
    print("=" * 50)

    if linkedin_result and instagram_result:
        print("🎉 SUCCESS: Both platforms should work now!")
    elif linkedin_result:
        print("✅ LinkedIn fixed, but Instagram broke")
    elif instagram_result:
        print("❌ LinkedIn still broken, Instagram works")
    else:
        print("💥 Both platforms broken")


if __name__ == "__main__":
    test_linkedin_response_fix()
