// TikTok video extraction functionality
function extractTikTokVideo(url) {
    console.log("🎵 Iniciando extracción de TikTok:", url);

    // Mostrar loading
    showLoadingState();

    // Enviar request al servidor
    fetch("/api/extract", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: url }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log("📱 Respuesta del servidor TikTok:", data);

            if (data.success) {
                // Mostrar el video
                displayVideo(data);
                console.log("✅ Video de TikTok cargado exitosamente");
            } else {
                // Mostrar error
                showError(data.error || "Error al extraer video de TikTok");
                console.error("❌ Error en extracción TikTok:", data.error);
            }
        })
        .catch((error) => {
            console.error("💥 Error de red TikTok:", error);
            showError("Error de conexión al extraer video de TikTok");
        })
        .finally(() => {
            // Ocultar loading
            hideLoadingState();
        });
}

// Validar URL de TikTok
function isValidTikTokUrl(url) {
    const tikTokPatterns = [
        /^https?:\/\/(www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+/,
        /^https?:\/\/vm\.tiktok\.com\/[A-Za-z0-9]+/,
        /^https?:\/\/(www\.)?tiktok\.com\/.*\/video\/\d+/,
    ];

    return tikTokPatterns.some((pattern) => pattern.test(url));
}

// Procesar URL de TikTok
function processTikTokUrl(url) {
    console.log("🔍 Procesando URL de TikTok:", url);

    if (!isValidTikTokUrl(url)) {
        showError(
            "URL de TikTok no válida. Usa enlaces como: https://www.tiktok.com/@usuario/video/123456789"
        );
        return false;
    }

    // Llamar a la función de extracción
    extractTikTokVideo(url);
    return true;
}

// Obtener información específica de TikTok para mostrar
function getTikTokVideoInfo(data) {
    return {
        title: data.title || "Video de TikTok",
        creator: data.uploader || "Usuario de TikTok",
        duration: data.duration || 0,
        views: data.view_count || 0,
        platform: "TikTok",
        thumbnail: data.thumbnail || "",
        videoUrl: data.video_url,
        quality: data.video_quality || "Desconocida",
    };
}

// Mostrar metadatos específicos de TikTok
function displayTikTokMetadata(videoInfo) {
    const metadata = document.querySelector(".video-metadata");
    if (metadata) {
        const viewsText =
            videoInfo.views > 0
                ? `${formatNumber(videoInfo.views)} visualizaciones`
                : "";
        const durationText =
            videoInfo.duration > 0
                ? `${formatDuration(videoInfo.duration)}`
                : "";

        metadata.innerHTML = `
            <div class="metadata-row">
                <span class="platform-badge tiktok">📱 TikTok</span>
                <span class="quality-badge">${videoInfo.quality}</span>
            </div>
            <div class="metadata-row">
                <span class="creator">👤 ${videoInfo.creator}</span>
                ${viewsText ? `<span class="views">👀 ${viewsText}</span>` : ""}
            </div>
            ${durationText
                ? `<div class="metadata-row"><span class="duration">⏱️ ${durationText}</span></div>`
                : ""
            }
        `;
    }
}

// Mostrar video de TikTok usando el mismo template que las otras plataformas
function showTikTokVideo(data, container) {
    console.log("🎵 Mostrando video de TikTok:", data);

    if (!data.videoUrl) {
        console.error("❌ No se encontró URL del video de TikTok");
        container.innerHTML = `<div class="error"><h3>No se encontró URL del video de TikTok</h3></div>`;
        return;
    }

    // Enable global download
    // Usamos original_url si existe para forzar descarga HQ por servidor, sino videoUrl directo
    const downloadUrl = data.original_url || data.videoUrl;
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadUrl, "tiktok_video.mp4");
    }

    // Usar el mismo template unificado que Instagram, LinkedIn y X
    const cardHtml = renderVideoCard({
        videoUrl: data.videoUrl,
        thumbnail: data.thumbnail
    });

    container.innerHTML = cardHtml;

    // Log de éxito
    console.log(
        "✅ Video de TikTok mostrado exitosamente con template unificado"
    );

    // Scroll hacia el video
    setTimeout(() => {
        container.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
}

// Función auxiliar para formatear números
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
}

// Función auxiliar para formatear duración
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
}

console.log("📱 TikTok extractor loaded successfully");
