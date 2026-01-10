
function showPinterestVideo(data, container) {
    container.innerHTML = "";
    const url = data.video_url || data.videoUrl || "";
    const type = data.type || 'video';
    const title = data.title || "Pinterest Pin";
    const thumbnail = data.thumbnail || "";

    if (!url) {
        container.innerHTML = `<div class="error"><h3>No se encontró contenido disponible</h3></div>`;
        return;
    }

    // Dynamic filename
    const safeTitle = title.replace(/[^a-z0-9áéíóúñ_-]/gi, '_').substring(0, 50);
    const extension = type === 'image' ? 'jpg' : 'mp4';
    const filename = `${safeTitle}.${extension}`;

    // Enable auto-download hook
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(url, filename);
    }

    // Solo renderizar la card de video sin información adicional
    const cardHtml = renderVideoCard({
        videoUrl: url,
        thumbnail: thumbnail,
        title: title
    });
    container.innerHTML = cardHtml;
}
