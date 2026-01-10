// Funciones específicas para X/Twitter - COPIANDO EXACTAMENTE LinkedIn
function showXVideo(data, container) {
    container.innerHTML = "";
    const videoUrl = data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(videoUrl, "twitter_video.mp4");
    }

    // Renderizar la tarjeta con preview igual que LinkedIn
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
        thumbnail: data.thumbnail,
        originalUrl: videoUrl, // Pass URL for smart download
        platform: 'x'
    });
    container.innerHTML = videoCardHTML;
}
