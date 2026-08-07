// Funciones específicas para Instagram
function showInstagramVideo(data, container) {
    const formats = data.video_formats || [];
    if (formats.length === 0) {
        container.innerHTML = `<div class="error"><h3>No se encontraron MP4s con audio</h3></div>`;
        return;
    }
    const format = formats[0];
    const previewUrl = data.preview_url || format.url;
    const downloadTarget = getDownloadTarget(data, previewUrl);

    const filename = buildFilename('instagram', data.title, 'mp4');

    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadTarget, filename);
    }

    // Solo renderizar la card de video sin información adicional
    const cardHtml = renderVideoCard({
        videoUrl: previewUrl,
        downloadTarget: downloadTarget,
        thumbnail: data.thumbnail,
        filename: filename,
        title: data.title || '',
        platform: 'instagram'
    });
    container.innerHTML = cardHtml;
}
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
