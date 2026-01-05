// Funciones específicas para Instagram
function showInstagramVideo(data, container) {
    const formats = data.video_formats || [];
    if (formats.length === 0) {
        container.innerHTML = `<div class="error"><h3>No se encontraron MP4s con audio</h3></div>`;
        return;
    }
    const format = formats[0];

    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(format.url, "instagram_video.mp4");
    }

    // Solo renderizar la card de video sin información adicional
    const cardHtml = renderVideoCard({
        videoUrl: format.url,
    });
    container.innerHTML = cardHtml;
}
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
