
function showPinterestVideo(data, container) {
    container.innerHTML = "";
    const url = data.preview_url || data.video_url || data.videoUrl || "";
    const type = data.type || 'video';
    const title = data.title || "Pinterest Pin";
    const thumbnail = data.thumbnail || "";

    if (!url) {
        container.innerHTML = `<div class="error"><h3>No se encontró contenido disponible</h3></div>`;
        return;
    }

    // Dynamic filename: pinterest_titulo_fecha.(mp4|jpg)
    const extension = type === 'image' ? 'jpg' : 'mp4';
    const filename = buildFilename('pinterest', title, extension);
    const downloadTarget = getDownloadTarget(data, url);

    // Enable auto-download hook
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadTarget, filename);
    }

    // Solo renderizar la card de video sin información adicional
    const cardHtml = renderVideoCard({
        videoUrl: url,
        thumbnail: thumbnail,
        title: title,
        downloadTarget: downloadTarget,
        filename: filename, // Pass the correct filename (with .jpg for images)
        type: type, // Pass type to handle play icon
        platform: 'pinterest'
    });
    container.innerHTML = cardHtml;
}
