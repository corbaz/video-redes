// JavaScript específico para YouTube/Shorts
// Optimizado para yt-dlp y template unificado

/**
 * Valida URLs de YouTube y Shorts
 */
function isValidYouTubeURL(url) {
    if (!url || typeof url !== "string") return false;

    // Patrones para YouTube y Shorts
    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/m\.youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
    ];

    return patterns.some((pattern) => pattern.test(url));
}

/**
 * Detecta si es un YouTube Short
 */
function isYouTubeShort(url) {
    return url.includes("/shorts/");
}

/**
 * Normaliza URLs de YouTube
 */
function normalizeYouTubeURL(url) {
    try {
        // Eliminar parámetros adicionales excepto v
        if (url.includes("youtube.com/watch")) {
            const urlObj = new URL(url);
            const videoId = urlObj.searchParams.get("v");
            if (videoId) {
                return `https://www.youtube.com/watch?v=${videoId}`;
            }
        }
        return url;
    } catch {
        return url;
    }
}

/**
 * Prepara datos específicos para YouTube
 */
function prepareYouTubeData(result) {
    const baseData = {
        title: result.title || "Video de YouTube",
        description: result.description || "",
        uploader: result.uploader || "Canal de YouTube",
        thumbnail: result.thumbnail || "",
        videoUrl: result.video_url || "",
        originalUrl: result.original_url || "",
        platform: result.platform || "YouTube",
        view_count: result.view_count || 0,
        like_count: result.like_count || 0,
        duration: result.duration || 0,
        video_quality: result.video_quality || "N/A",
        max_quality: result.max_quality || result.video_quality || "N/A",
        is_short: result.is_short || false,
    };

    // Añadir información específica de Shorts
    if (baseData.is_short) {
        baseData.platform = "YouTube Short";
        baseData.shortInfo = "📱 YouTube Short";
    }

    return baseData;
}

/**
 * Función principal para extraer videos de YouTube
 */
async function extractYouTubeVideo(url) {
    // Mostrar loading específico para YouTube
    showLoading("youtube");

    try {
        // Validar URL
        if (!isValidYouTubeURL(url)) {
            throw new Error(
                "URL de YouTube no válida. Usa enlaces de videos o Shorts de YouTube."
            );
        }

        // Normalizar URL
        const normalizedUrl = normalizeYouTubeURL(url);

        // Detectar tipo de contenido
        const isShort = isYouTubeShort(normalizedUrl);
        console.log(
            `🎥 Extrayendo ${isShort ? "YouTube Short" : "video de YouTube"
            }: ${normalizedUrl}`
        );

        // Realizar extracción
        const response = await fetch("/extract", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url: normalizedUrl }),
        });

        const result = await response.json();

        if (result.success) {
            // Preparar datos para template unificado
            const videoData = prepareYouTubeData(result);

            // Renderizar usando template unificado
            renderVideoCard(videoData);

            // Log para debugging
            console.log(
                `✅ Extracción exitosa de ${videoData.platform}:`,
                videoData.title
            );

            // Estadísticas específicas de YouTube
            if (videoData.view_count || videoData.like_count) {
                console.log(
                    `📊 Vistas: ${formatNumber(
                        videoData.view_count
                    )}, Likes: ${formatNumber(videoData.like_count)}`
                );
            }
        } else {
            throw new Error(
                result.error || "Error desconocido al extraer video de YouTube"
            );
        }
    } catch (error) {
        console.error("❌ Error extrayendo video de YouTube:", error);
        showError(error.message, "youtube");
    } finally {
        hideLoading();
    }
}

/**
 * Formatear números grandes (vistas, likes)
 */
function formatNumber(num) {
    if (!num || num === 0) return "0";

    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
}

/**
 * Mostrar loading específico para YouTube
 */
function showLoading(platform) {
    const loadingHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <div class="loading-text">
                <h3>🎥 Extrayendo de YouTube</h3>
                <p>Procesando video con yt-dlp...</p>
                <small>Esto puede tomar unos segundos</small>
            </div>
        </div>
    `;

    const container = document.getElementById("result");
    if (container) {
        container.innerHTML = loadingHTML;
        container.style.display = "block";
    }
}

/**
 * Mostrar error específico para YouTube
 */
function showError(message, platform) {
    // Helper para escapar HTML y prevenir XSS
    const escapeHTML = (str) => {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    const safeMessage = escapeHTML(message);

    const errorHTML = `
        <div class="error-container">
            <div class="error-icon">❌</div>
            <div class="error-content">
                <h3>Error con YouTube</h3>
                <p>${safeMessage}</p>
                <div class="error-suggestions">
                    <h4>💡 Sugerencias:</h4>
                    <ul>
                        <li>Verifica que el video sea público</li>
                        <li>Intenta con videos sin restricciones</li>
                        <li>Asegúrate de usar enlaces válidos de YouTube</li>
                        <li>Para Shorts, usa enlaces de /shorts/</li>
                    </ul>
                </div>
            </div>
        </div>
    `;

    const container = document.getElementById("result");
    if (container) {
        container.innerHTML = errorHTML;
        container.style.display = "block";
    }
}

/**
 * Ocultar loading
 */
function hideLoading() {
    // El loading se oculta automáticamente cuando se renderiza el resultado
    // Esta función existe por consistencia con otros archivos
}

/**
 * Mostrar video de YouTube con UI simplificada:
 * - Imagen estática (sin video interactivo)
 * - Botón de descargar junto a estadísticas
 */
function showYouTubeVideo(data, container) {
    console.log("🎥 Renderizando tarjeta HQ para YouTube:", data);

    if (!data.videoUrl && !data.video_url) {
        container.innerHTML = `<div class="error"><h3>No se encontró información del video</h3></div>`;
        return;
    }

    // Helper para escapar HTML
    const escapeHTML = (str) => {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    // Datos procesados
    const rawTitle = data.title || "Video de YouTube";
    const title = escapeHTML(rawTitle);

    // Thumbnail Fallback Logic
    let thumbnail = data.thumbnail;
    if (!thumbnail || thumbnail === "") {
        // Try to construct high-res thumbnail if video_id is present
        // (Assuming extract_video_info might pass id, otherwise generic)
        if (data.id) {
            thumbnail = `https://img.youtube.com/vi/${data.id}/maxresdefault.jpg`;
        } else {
            // Generic placeholder or low-res from data
            thumbnail = "https://via.placeholder.com/800x450/000000/FFFFFF?text=No+Thumbnail";
        }
    } else {
        // Fix for YouTube webp thumbnails which might not load in some contexts
        // Convert https://i.ytimg.com/vi_webp/ID/maxresdefault.webp -> https://i.ytimg.com/vi/ID/maxresdefault.jpg
        if (thumbnail.includes('i.ytimg.com')) {
            thumbnail = thumbnail.replace('/vi_webp/', '/vi/').replace('.webp', '.jpg');
        }
    }

    console.log("📷 Thumbnail URL fixed:", thumbnail);

    const originalUrl = data.original_url || data.originalUrl || data.video_url;
    // Sanitizar nombre de archivo
    const safeTitle = rawTitle.replace(/[\\/:*?"<>|]/g, "").trim() || "video";
    const filename = encodeURIComponent(safeTitle + ".mp4");

    // Enable Global Download Button
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(originalUrl, filename);
    }

    // Check global download button status
    const btnd = document.getElementById('mainDownloadBtn');
    if (btnd) console.log("Download button href:", btnd.href);

    // Force container display
    if (container.style.display === 'none') {
        container.style.display = 'block';
    }

    // Template Pro UI (Usa clases CSS robustas)
    // Add onclick handler to trigger smart download
    const clickHandler = `onclick="if(window.startSmartDownload) { window.startSmartDownload('${originalUrl}', '${filename}'); } else { console.error('SmartDownload not found'); }"`;

    container.innerHTML = `
        <div class="pro-video-card">
            <div class="pro-video-card-inner" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
                <img src="${thumbnail}" alt="${title}" class="pro-video-card-img"
                     onerror="if (this.src.includes('maxresdefault')) { this.src = this.src.replace('maxresdefault.jpg', 'hqdefault.jpg'); } else { this.src = 'https://via.placeholder.com/800x450/000000/FFFFFF?text=No+Thumbnail'; }">
                
                <!-- Play Icon Overlay -->
                <div class="card-play-icon" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 3em; color: rgba(255, 255, 255, 0.9); z-index: 20; text-shadow: 0 4px 8px rgba(0,0,0,0.5);">▶️</div>
                
                <!-- Glossy Overlay Effect -->
                <div class="pro-video-glossy-overlay">
                </div>
            </div>
        </div>
    `;

    // Log
    console.log("✅ UI de YouTube renderizada (Simplificada: Solo Calidad + Descarga)", container);

    // Scroll
    setTimeout(() => {
        container.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
}

// Exportar funciones para uso global
if (typeof window !== "undefined") {
    window.extractYouTubeVideo = extractYouTubeVideo;
    window.isValidYouTubeURL = isValidYouTubeURL;
    window.isYouTubeShort = isYouTubeShort;
}

console.log("📺 YouTube.js cargado - Modo HQ UI Simplificada");
