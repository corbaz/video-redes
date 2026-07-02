// Funciones específicas para X/Twitter - COPIANDO EXACTAMENTE LinkedIn
function showXVideo(data, container) {
    container.innerHTML = "";
    const videoUrl = data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    const filename = buildFilename('x', data.title, 'mp4');
    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(videoUrl, filename);
    }

    // Renderizar la tarjeta con preview igual que LinkedIn
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
        thumbnail: data.thumbnail,
        originalUrl: videoUrl, // Pass URL for smart download
        filename: filename,
        title: data.title || '',
        platform: 'x'
    });
    container.innerHTML = videoCardHTML;
}
