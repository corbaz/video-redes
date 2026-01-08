// Facebook video extraction functionality
function extractFacebookVideo(url) {
    console.log("📘 Iniciando extracción de Facebook:", url);

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
            console.log("📘 Respuesta del servidor Facebook:", data);

            if (data.success) {
                // Mostrar el video usando el template unificado
                displayVideo(data);
                console.log("✅ Video de Facebook cargado exitosamente");
            } else {
                // Mostrar error
                showError(data.error || "Error al extraer video de Facebook");
                console.error("❌ Error en extracción Facebook:", data.error);
            }
        })
        .catch((error) => {
            console.error("💥 Error de red Facebook:", error);
            showError("Error de conexión al extraer video de Facebook");
        })
        .finally(() => {
            // Ocultar loading
            hideLoadingState();
        });
}

// Validar URL de Facebook
function isValidFacebookUrl(url) {
    const facebookPatterns = [
        /^https?:\/\/(www\.)?facebook\.com\/.*\/videos?\//,
        /^https?:\/\/(www\.)?facebook\.com\/.*\/posts?\//,
        /^https?:\/\/(www\.)?facebook\.com\/share\//,
        /^https?:\/\/(www\.)?facebook\.com\/watch\//,
        /^https?:\/\/fb\.watch\//,
        /^https?:\/\/m\.facebook\.com\//,
    ];

    return facebookPatterns.some((pattern) => pattern.test(url));
}

// Mostrar video de Facebook usando el mismo template que las otras plataformas
function showFacebookVideo(data, container) {
    console.log("📘 Mostrando video de Facebook:", data);

    if (!data.videoUrl) {
        console.error("❌ No se encontró URL del video de Facebook");
        container.innerHTML = `<div class="error"><h3>No se encontró URL del video de Facebook</h3></div>`;
        return;
    }

    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(data.videoUrl, "facebook_video.mp4");
    }

    // Usar el mismo template unificado que Instagram, LinkedIn, X y TikTok
    const cardHtml = renderVideoCard({
        videoUrl: data.videoUrl,
        thumbnail: data.thumbnail
    });

    container.innerHTML = cardHtml;

    // Log de éxito
    console.log(
        "✅ Video de Facebook mostrado exitosamente con template unificado"
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

console.log("📘 Facebook extractor loaded successfully");
