// Funciones específicas para X/Twitter - COPIANDO EXACTAMENTE LinkedIn
function showXVideo(data, container) {
    container.innerHTML = "";
    const videoUrl = data.preview_url || data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    const filename = buildFilename('x', data.title, 'mp4');
    const downloadTarget = getDownloadTarget(data, videoUrl);
    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadTarget, filename);
    }

    // Renderizar la tarjeta con preview igual que LinkedIn
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
        thumbnail: data.thumbnail,
        downloadTarget: downloadTarget,
        filename: filename,
        title: data.title || '',
        platform: 'x'
    });
    container.innerHTML = videoCardHTML;
}
