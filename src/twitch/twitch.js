// twitch.js - Manejo frontend para Twitch

function isValidTwitchUrl(url) {
    return url.includes('twitch.tv') || url.includes('twitch.com');
}

function showTwitchVideo(data, container) {
    console.log("💜 Mostrando video de Twitch:", data);

    const previewUrl = data.preview_url || data.videoUrl;
    if (!previewUrl) {
        console.error("❌ No se encontró URL del video de Twitch");
        container.innerHTML = `<div class="error"><h3>No se encontró URL del video de Twitch</h3></div>`;
        return;
    }

    // Enable global download
    // Usamos original_url para forzar descarga HQ por servidor a través de yt-dlp
    const downloadTarget = getDownloadTarget(data, previewUrl, 'source');
    const filename = buildFilename('twitch', data.title, 'mp4');
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadTarget, filename);
    }

    // Usar el mismo template unificado
    // data.thumbnail debería venir del extractor
    const cardHtml = renderVideoCard({
        videoUrl: previewUrl, // En el caso de Twitch, esto puede ser un m3u8, pero renderVideoCard prioriza thumbnail
        thumbnail: data.thumbnail,
        title: data.title,
        filename: filename,
        downloadTarget: downloadTarget,
        duration: data.duration,
        platform: 'twitch',
        views: data.view_count,
        uploader: data.uploader
    });

    container.innerHTML = cardHtml;

    console.log("✅ Video de Twitch mostrado exitosamente");
}
