# 📹 Multi-Platform Video Downloader

## 🌟 Plataformas Soportadas

✅ **Instagram** - Posts y Reels  
✅ **LinkedIn** - Videos de posts  
✅ **X/Twitter** - Videos de tweets  
✅ **TikTok** - Videos y contenido  
✅ **Facebook** - Videos públicos  
✅ **YouTube** - Videos y Shorts (CALIDAD OPTIMIZADA)  

## 🚀 Características Principales

- **UI/UX Unificada**: Misma experiencia para todas las plataformas
- **Calidad Optimizada**: YouTube descarga automáticamente la mejor calidad disponible (hasta 1080p) con audio incluido
- **Extractores Robustos**: Sistema de fallback para máxima compatibilidad
- **Logging Detallado**: Información completa de resolución, bitrate y calidad
- **Interfaz Responsiva**: Diseño moderno y adaptable
- **API REST**: Endpoints para validación y extracción

## 🎥 YouTube - Calidad Optimizada

El extractor de YouTube implementa un sistema de múltiples formatos para garantizar la mejor calidad:

1. **bestvideo[height<=1080]+bestaudio** - Máxima calidad con audio
2. **best[height<=1080][ext=mp4]** - Formato MP4 de alta calidad  
3. **bestvideo[height>=720]+bestaudio** - Calidad HD con audio
4. **bestvideo[height>=480]+bestaudio** - Calidad media con audio
5. **best** - Mejor calidad disponible como último recurso

### Resoluciones Objetivo
- 🎯 **1080p** (Preferido)
- 🎯 **720p** (Muy buena calidad)
- 🎯 **480p** (Calidad estándar)
- 🎯 **Auto** (Mejor disponible)

## 🚀 Instalación y Uso

### 1. Requisitos

```bash
# Instalar Python 3.7+ y yt-dlp
pip install yt-dlp

# O si no tienes pip:
python -m pip install yt-dlp
```

### 2. Ejecutar el Servidor

```bash
# Opción 1: Puerto por defecto (8000)
python server.py

# Opción 2: Puerto personalizado
python server.py 8080
```

### 3. Acceder a la Aplicación

```
http://localhost:8000
```

## 🧪 Probar con CURL

### Verificar que el servidor funciona

```bash
curl http://localhost:8000/api/health
```

### Probar con la URL problemática

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/reel/DC2s8l_R-jr/"}' \
  | python3 -m json.tool
```

**Resultado esperado** (JSON válido, NO error XML):

```json
{
  "success": false,
  "error": "Instagram authentication required",
  "error_type": "auth_required",
  "suggestion": "This content requires login. Try with public videos from verified accounts."
}
```

## 🔧 Qué Se Arregló

### Antes (Roto)

- ❌ Error: "Unexpected token '<', \"<?xml vers\"... is not valid JSON"
- ❌ Aplicación crasheaba con errores técnicos
- ❌ No había manera de entender qué pasaba

### Ahora (Arreglado)

- ✅ **Respuestas JSON garantizadas** en todos los casos
- ✅ **Manejo elegante de errores** con mensajes útiles
- ✅ **Múltiples capas de protección** contra crashes
- ✅ **Detección de tipo de respuesta** antes de parsear
- ✅ **Mensajes específicos** según el tipo de error

## 💡 URLs que Funcionan Mejor

### ✅ Recomendadas

- Videos de cuentas públicas populares
- Contenido de cuentas verificadas (✓)
- Videos antiguos con muchas interacciones
- Videos educativos o promocionales

### ⚠️ Pueden fallar

- Videos muy recientes (menos de 24h)
- Contenido de cuentas privadas
- Videos con restricciones especiales
- URLs con muchos parámetros de tracking

## 🆘 Resolución de Problemas

### Error: "yt-dlp not found"

```bash
pip install yt-dlp
# o
python3 -m pip install yt-dlp
```

### Error: "Port already in use"

```bash
# Usar otro puerto
python3 server.py 8001
```

### Error: "Permission denied"

```bash
# En Linux/Mac, dar permisos:
chmod +x server.py
```

## 📊 Características Técnicas

- **Backend**: Python 3 con manejo bulletproof de errores
- **Frontend**: HTML5 + JavaScript moderno
- **Extractor**: yt-dlp con múltiples estrategias de fallback
- **Respuestas**: JSON garantizado en 100% de casos
- **Errores**: Categorizados y con sugerencias específicas

## 🎯 Endpoints de API

- `GET /api/health` - Estado del servidor
- `POST /api/validate` - Validar URL de Instagram  
- `POST /api/extract` - Extraer información del video

## ⚠️ Aviso Legal

Esta herramienta es para uso personal únicamente:

- Respeta los derechos de autor
- Cumple con las políticas de Instagram
- No redistribuyas contenido sin permiso
- Usa responsablemente

---

**Versión**: 1.0.0-fixed  
**Estado**: ✅ Error XML completamente eliminado  
**Garantía**: 100% respuestas JSON válidas

```json
{
  "id": "DC2s8l_R-jr",
  "title": "¿QUE OPINAS DE ESTO? 🤯 La IA está fuera de control, ya es capaz de crear videos híper realistas en cuestión de MINUTOS 🤖🔥 PASO A PASO: 1. Comenta \"VIDEO\" y te comparto el enlace de esta IA 2. Créate una cuenta gratis 3. Pon un Prompt o imagen de referencia 4. Dale a generar (6 videos gratis po",
  "description": "¿QUE OPINAS DE ESTO? 🤯\n\nLa IA está fuera de control, ya es capaz de crear videos híper realistas en cuestión de MINUTOS 🤖🔥\n\nPASO A PASO:\n\n1. Comenta \"VIDEO\" y te comparto el enlace de esta IA\n2. Créate una cuenta gratis\n3. Pon un Prompt o imagen de referencia\n4. Dale a generar (6 videos gratis po",
  "uploader": "Melisa Escobar | Vender con IA 🤖",
  "uploader_id": "melisaescobart",
  "uploader_url": "https://www.instagram.com/melisaescobart",
  "duration": 44.8,
  "view_count": 23614,
  "like_count": 23614,
  "tags": [
    "ia", "data", "bigdata", "inteligenciaartificial", "chatgpt", "openai", "automatizacion", "eficiencia", "bilbao", "inspiracion", "motivacion"
  ],
  "formats": [
    {
      "format_id": "1333p",
      "url": "https://scontent-...mp4",
      "ext": "mp4",
      "width": 750,
      "height": 1333,
      "filesize": null,
      "vcodec": "avc1.64001F",
      "acodec": "mp4a.40.2",
      "abr": null,
      "audio_channels": 2,
      "fps": 30,
      "format_note": "1333p",
      "audio_ext": "m4a"
    }
  ],
  "thumbnail": "https://instagram.fxyz1-1.fna.fbcdn.net/v/t51.2885-15/...",
  "webpage_url": "https://www.instagram.com/reel/DC2s8l_R-jr/",
  "timestamp": 1717950000,
  "upload_date": "20250609"
}
```
---
``` bash
c:\www\insta\
├── .git/                   # Control de versiones
├── .gitignore              # Exclusiones (temporales, logs, videos)
├── card.js                 # Template unificado de video
├── facebook.js             # Frontend Facebook
├── facebook_extractor.py   # Backend Facebook
├── favicon.ico             # Icono de la app
├── index.html              # Frontend principal
├── insta.js                # Frontend Instagram
├── insta_extractor.py      # Backend Instagram
├── linkedin.js             # Frontend LinkedIn
├── linkedin_extractor.py   # Backend LinkedIn
├── p.bat                   # Script de inicio
├── README.md               # Documentación completa
├── requirements.txt        # Dependencias Python
├── server.log              # Log del servidor (excluido en git)
├── server.py               # Servidor principal
├── tiktok.js               # Frontend TikTok
├── tiktok_extractor.py     # Backend TikTok
├── x.js                    # Frontend X/Twitter
├── x_extractor.py          # Backend X/Twitter
├── youtube.js              # Frontend YouTube
└── youtube_extractor.py    # Backend YouTube (OPTIMIZADO)
```
---

