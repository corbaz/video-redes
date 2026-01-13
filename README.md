# 📹 Multi-Platform Video Downloader

## 🌟 Plataformas Soportadas

✅ **Instagram** - Posts, Reels, Stories y Videos Privados (con manejo de cookies)
✅ **LinkedIn** - Videos de posts y Galerías de imágenes (descarga secuencial)
✅ **X (Twitter)** - Videos de tweets (alta calidad garantizada)
✅ **TikTok** - Videos sin marca de agua
✅ **Facebook** - Videos públicos y Reels
✅ **YouTube** - Videos y Shorts (Calidad Optimizada hasta 1080p + Audio)
✅ **Pinterest** - Videos e Imágenes (Pin original)
✅ **Twitch** - Clips y VODs

## 🚀 Características Principales

- **UI/UX Unificada**: Misma experiencia para todas las plataformas desde una sola interfaz.
- **Calidad Optimizada**:
  - YouTube: Selección inteligente de video (1080p/720p) + audio fusionado.
  - X/Twitter: Enrutamiento especial para evitar errores 403.
  - Instagram: Soporte para historias y cuentas privadas (usando cookies del navegador).
- **Descargas Inteligentes**:
  - LinkedIn: Detecta si es video o galería. Si es galería, descarga imágenes secuencialmente (img-1, img-2...).
  - Archivos ZIP: Empaquetado automático para descargas múltiples.
- **Interfaz Responsiva**: Diseño moderno, adaptable a móviles y escritorio.
- **Logging Detallado**: Información completa de resolución, bitrate y errores en consola.
- **API REST Local**: Endpoints para validación y extracción, listos para integración.

## 📂 Estructura del Proyecto

El proyecto está modularizado para facilitar el mantenimiento:

```bash
c:\www\video-redes\
├── src/
│   ├── common/             # Estilos y scripts compartidos
│   ├── facebook/           # Módulo Facebook
│   ├── instagram/          # Módulo Instagram (incluye soporte Cookies)
│   ├── linkedin/           # Módulo LinkedIn (incluye soporte Galerías)
│   ├── pinterest/          # Módulo Pinterest
│   ├── tiktok/             # Módulo TikTok
│   ├── twitch/             # Módulo Twitch
│   ├── x/                  # Módulo X (Twitter)
│   ├── youtube/            # Módulo YouTube
│   └── server.py           # Servidor principal (Entry Point)
├── .venv/                  # Entorno virtual (no incluido en git)
├── index.html              # Frontend principal
├── p.ps1                   # Script de inicio rápido (PowerShell)
├── Procfile                # Configuración para despliegue (Railway/Heroku)
├── requirements.txt        # Dependencias del proyecto
└── runtime.txt             # Versión de Python para la nube
```

## �️ Instalación y Uso Local

### 1. Prerrequisitos

*   **Python 3.11+**: Asegúrate de tener Python instalado y agregado al PATH.
*   **FFmpeg**: Necesario para unir video y audio en alta calidad (especialmente para YouTube).
    *   *Windows*: Descargar de [ffmpeg.org](https://ffmpeg.org/download.html) y agregar `bin` al PATH.

### 2. Configuración Inicial

1.  **Clonar/Descargar** el repositorio en tu carpeta de trabajo (ej: `c:\www\video-redes`).
2.  **Crear entorno virtual** (Recomendado):
    ```powershell
    python -m venv .venv
    ```
3.  **Activar entorno**:
    ```powershell
    # Windows (PowerShell)
    .\.venv\Scripts\Activate.ps1
    ```
4.  **Instalar dependencias**:
    ```powershell
    pip install -r requirements.txt
    ```

### 3. Ejecutar el Servidor

Tienes dos opciones:

**Opción A: Script Automático (Recomendado)**
Ejecuta el script `p.ps1` en PowerShell. Este script limpia procesos antiguos, activa el entorno y lanza el servidor.
```powershell
.\p.ps1
```

**Opción B: Manual**
```powershell
# Asegúrate de tener el entorno activado
python src/server.py
```

### 4. Usar la Aplicación

1.  Abre tu navegador y ve a:
    ```
    http://localhost:8000
    ```
2.  Pega el enlace de la red social (Instagram, TikTok, YouTube, etc.).
3.  El sistema detectará automáticamente la plataforma.
4.  Haz clic en **"Buscar Video"** para ver la vista previa.
5.  Haz clic en **"Descargar Video"** (o "Descargar Imágenes" en caso de galerías).

---

## ☁️ Despliegue en la Nube (Railway/Heroku)

El proyecto está configurado para desplegarse fácilmente ("Deploy Ready").

1.  **Archivos Clave**:
    *   `Procfile`: Indica el comando de inicio (`web: python src/server.py`).
    *   `runtime.txt`: Fija la versión de Python (`python-3.11`).
    *   `requirements.txt`: Lista de librerías necesarias.
    *   `server.py`: Configurado para leer el puerto de la variable de entorno `PORT`.

2.  **Pasos para Railway**:
    *   Sube tu código a GitHub.
    *   Crea nuevo proyecto en Railway desde GitHub.
    *   Railway detectará el `Procfile` y desplegará automáticamente.

---

## 🆘 Solución de Problemas Comunes

### Error: "Instagram authentication required" / "Private account"
*   **Causa**: Estás intentando bajar una historia o un video de una cuenta privada.
*   **Solución**: El servidor intentará usar las cookies de tu navegador (Chrome/Edge) localmente. Asegúrate de haber iniciado sesión en Instagram en tu navegador predeterminado.
*   *Nota*: Si el error persiste ("Permission denied"), cierra el navegador completamente para liberar el archivo de cookies y reintenta.

### Error: "403 Forbidden" en X/Twitter
*   **Solución**: Ya está parchado internamente. El sistema usa `twimg.com` para evitar el bloqueo de `x.com`.

### Error: "FFmpeg not found"
*   **Solución**: Instala FFmpeg y agrégalo a tus variables de entorno. Sin esto, los videos de YouTube de alta calidad (1080p) se descargarán sin audio o en baja resolución.

### La descarga es lenta en local
*   **Causa**: El video se descarga primero a tu carpeta temporal y luego se te envía.
*   **Normalidad**: Es el comportamiento esperado para garantizar que el archivo final esté limpio y tenga el nombre correcto.

---

## ⚠️ Aviso Legal

Esta herramienta ha sido creada con fines educativos y de uso personal.
*   Respeta los derechos de autor y la propiedad intelectual.
*   No descargues ni redistribuyas contenido privado sin consentimiento.
*   El usuario es responsable del uso que le dé a esta herramienta.
