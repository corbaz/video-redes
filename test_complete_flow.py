#!/usr/bin/env python3
"""
Test completo que simula el flujo frontend -> backend -> extractor -> frontend
"""

from insta_extractor import InstagramExtractor
from linkedin_extractor import LinkedInExtractor
import json
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.insert(0, os.path.dirname(__file__))


def simulate_frontend_request(url):
    """Simula una petición completa del frontend"""
    print(f"🌐 Frontend: Usuario ingresa URL: {url}")

    # 1. Validación (simulada)
    print("📡 Frontend: Enviando a /api/validate")
    if 'linkedin.com' in url or 'instagram.com' in url:
        validate_response = {
            "success": True,
            "url": url,
            "platform": "linkedin" if 'linkedin.com' in url else "instagram"
        }
    else:
        validate_response = {
            "success": False,
            "error": "URL no válida"
        }

    print(
        f"📨 Backend responde validate: {json.dumps(validate_response, indent=2)}")

    if not validate_response["success"]:
        print("❌ Frontend: Validación falló")
        return

    # 2. Extracción (simulada)
    print("📡 Frontend: Enviando a /api/extract")

    if 'linkedin.com' in url:
        extractor = LinkedInExtractor()
        extract_response = extractor.extract_info(url)
    else:
        extractor = InstagramExtractor()
        extract_response = extractor.extract_info(url)

    print(
        f"📨 Backend responde extract: {json.dumps(extract_response, indent=2)}")

    # 3. Procesamiento en el frontend (simulado)
    print("🌐 Frontend: Procesando respuesta...")

    if extract_response.get("success"):
        data = extract_response.get("data")
        print(f"   extractResponse.success = {extract_response['success']}")
        print(f"   extractResponse.data = {data}")

        if data:
            print("✅ Frontend: Llamando showSuccess(data)")
            simulate_show_success(data, url)
        else:
            print("❌ Frontend: ERROR - data es None/undefined")
            print("   Mostrando error: 'El servidor indicó éxito pero no devolvió datos'")
    else:
        error = extract_response.get("error", "Error desconocido")
        print(f"❌ Frontend: Extracción falló - {error}")


def simulate_show_success(data, url):
    """Simula la función showSuccess del frontend"""
    print(f"🎯 showSuccess() llamada con data: {json.dumps(data, null=2)}")

    if not data:
        print("❌ ERROR: showSuccess recibió data undefined/null")
        return

    if 'linkedin.com' in url:
        video_url = extract_video_url(data)
        print(f"🔗 LinkedIn: videoUrl extraída = {video_url}")

        if video_url:
            print(
                f"✅ showLinkedinVideo({{'videoUrl': '{video_url}'}}) sería llamada")
        else:
            print("❌ ERROR: No se pudo extraer videoUrl de LinkedIn")
    else:
        print(f"📷 Instagram: showInstagramVideo(data) sería llamada")


def extract_video_url(data):
    """Simula la función extractVideoUrl del frontend"""
    if data.get('videoUrl'):
        return data['videoUrl']
    if data.get('data') and data['data'].get('videoUrl'):
        return data['data']['videoUrl']
    if data.get('url'):
        return data['url']
    if data.get('video_url'):
        return data['video_url']

    # Buscar en arrays de formatos
    if data.get('video_formats') and len(data['video_formats']) > 0:
        return data['video_formats'][0].get('url')
    if data.get('data') and data['data'].get('video_formats') and len(data['data']['video_formats']) > 0:
        return data['data']['video_formats'][0].get('url')

    return None


def main():
    """Ejecuta tests completos"""
    print("🧪 TESTING COMPLETE FLOW")
    print("=" * 60)

    test_urls = [
        "https://www.linkedin.com/posts/success-simulation",  # Debería funcionar
        "https://www.linkedin.com/posts/test-post",           # Debería fallar
        "https://www.instagram.com/p/test-post",              # Debería fallar
        "https://www.youtube.com/watch?v=invalid"             # URL inválida
    ]

    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/4: {url}")
        print("=" * 60)

        try:
            simulate_frontend_request(url)
        except Exception as e:
            print(f"❌ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()

        print("✅ Test completado")

    print(f"\n{'='*60}")
    print("🏁 TODOS LOS TESTS COMPLETADOS")
    print("=" * 60)


if __name__ == "__main__":
    main()
