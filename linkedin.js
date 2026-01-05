// Funciones específicas para LinkedIn - Updated 2025-06-10
function showLinkedinVideo(data, container) {
    container.innerHTML = "";
    const videoUrl = data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(videoUrl, "linkedin_video.mp4");
    }

    // Renderizar la tarjeta con preview igual que Instagram
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
    });
    container.innerHTML = videoCardHTML;
}
