// Funciones específicas para Threads
function showThreadsVideo(data, container) {
    const formats = data.video_formats || [];
    if (formats.length === 0) {
        container.innerHTML = `<div class="error"><h3>No se encontró video en el post de Threads</h3></div>`;
        return;
    }
    const format = formats[0];
    const previewUrl = data.preview_url || format.url;
    const downloadTarget = getDownloadTarget(data, previewUrl, 'direct');

    const filename = buildFilename('threads', data.title, 'mp4');

    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadTarget, filename);
    }

    const cardHtml = renderVideoCard({
        videoUrl: previewUrl,
        downloadTarget: downloadTarget,
        thumbnail: data.thumbnail,
        filename: filename,
        title: data.title || '',
        platform: 'threads'
    });
    container.innerHTML = cardHtml;
}
