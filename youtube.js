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
    const errorHTML = `
        <div class="error-container">
            <div class="error-icon">❌</div>
            <div class="error-content">
                <h3>Error con YouTube</h3>
                <p>${message}</p>
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
 * Mostrar video de YouTube usando el mismo template que las otras plataformas
 */
function showYouTubeVideo(data, container) {
    console.log("🎥 Mostrando video de YouTube:", data);

    if (!data.videoUrl && !data.video_url) {
        console.error("❌ No se encontró URL del video de YouTube");
        container.innerHTML = `<div class="error"><h3>No se encontró URL del video de YouTube</h3></div>`;
        return;
    }

    // Preparar datos enriquecidos con información de calidad
    const enrichedData = {
        videoUrl: data.video_url || data.videoUrl,
        originalUrl: data.original_url || data.originalUrl || data.video_url || data.videoUrl,
        title: data.title || "Video de YouTube",
        uploader: data.uploader || "Canal de YouTube",
        platform: data.platform || "YouTube",
        thumbnail: data.thumbnail || "",
        // Información adicional de calidad
        qualityInfo: {
            selected: data.quality_label || data.video_quality || "Auto",
            maxQuality: data.max_quality || "N/A",
            available: data.available_qualities || [],
            filesize: data.filesize || "N/A",
            format: data.selected_format || {},
        },
    };

    // Usar el mismo template unificado que todas las otras plataformas
    const cardHtml = renderVideoCard(enrichedData);

    container.innerHTML = cardHtml;

    // Añadir información adicional de calidad si está disponible
    if (data.available_qualities && data.available_qualities.length > 0) {
        addQualityInfo(container, data);
    }

    // Log de éxito con información de calidad
    console.log(
        "✅ Video de YouTube mostrado exitosamente con template unificado"
    );
    console.log(`📊 Calidad seleccionada: ${data.quality_label || "Auto"}`);
    console.log(
        `📋 Calidades disponibles: ${data.available_qualities
            ? data.available_qualities.join(", ")
            : "N/A"
        }`
    );

    // Scroll hacia el video
    setTimeout(() => {
        container.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
}

/**
 * Añade información adicional de calidad al contenedor
 */
function addQualityInfo(container, data) {
    const qualityInfoDiv = document.createElement("div");
    qualityInfoDiv.className = "youtube-quality-info";
    qualityInfoDiv.style.cssText = `
        margin-top: 10px;
        padding: 15px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        border-left: 3px solid #ff0000;
    `;

    const qualitySelected = data.quality_label || "Auto";
    const availableQualities = data.available_qualities || [];
    const filesize = data.filesize !== "N/A" ? data.filesize : null;

    qualityInfoDiv.innerHTML = `
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="color: #ff0000; margin-right: 8px;">🎯</span>
            <strong style="color: #fff;">Calidad seleccionada: ${qualitySelected}</strong>
        </div>
        ${filesize
            ? `
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="color: #ff0000; margin-right: 8px;">📁</span>
            <span style="color: #ccc;">Tamaño: ${filesize}</span>
        </div>
        `
            : ""
        }
        ${availableQualities.length > 0
            ? `
        <div style="display: flex; align-items: center;">
            <span style="color: #ff0000; margin-right: 8px;">📊</span>
            <span style="color: #ccc;">Calidades disponibles: ${availableQualities.join(
                ", "
            )}</span>
        </div>
        `
            : ""
        }
    `;

    // Insertar después del video
    const videoCard =
        container.querySelector(".video-card") ||
        container.querySelector(".cinema-player");
    if (videoCard) {
        videoCard.appendChild(qualityInfoDiv);
    }
}

// Exportar funciones para uso global
if (typeof window !== "undefined") {
    window.extractYouTubeVideo = extractYouTubeVideo;
    window.isValidYouTubeURL = isValidYouTubeURL;
    window.isYouTubeShort = isYouTubeShort;
}

console.log("📺 YouTube.js cargado - Soporte para videos y Shorts");
