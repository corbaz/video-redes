// Funciones específicas para Instagram
function showInstagramVideo(data, container) {
    const formats = data.video_formats || [];
    if (formats.length === 0) {
        container.innerHTML = `<div class="error"><h3>No se encontraron MP4s con audio</h3></div>`;
        return;
    }
    const format = formats[0];
    const videoInfo = `${format.width || ""}x${format.height || ""}`;

    // Extraer el nombre de usuario del título si comienza con "Video by"
    let title = data.title;
    let videoByUser = "";
    if (title && title.startsWith("Video by")) {
        const parts = title.split(" ");
        if (parts.length >= 3) {
            videoByUser = parts.slice(2).join(" ");
            title = ""; // Limpiar el título original
        }
    }

    const cardHtml = renderVideoCard({
        title: title,
        uploader: data.uploader,
        uploader_id: videoByUser || data.channel || data.uploader_id,
        uploader_url: data.channel
            ? `https://www.instagram.com/${data.channel}`
            : "",
        upload_date: data.upload_date,
        duration: data.duration ? formatDuration(data.duration) : "",
        likes: data.like_count?.toLocaleString() ?? "",
        comments: data.comment_count?.toLocaleString() ?? "",
        views: data.view_count?.toLocaleString() ?? "",
        videoUrl: format.url,
        videoInfo,
        description: data.description,
        tags: data.tags,
    });
    container.innerHTML = cardHtml;
}
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
