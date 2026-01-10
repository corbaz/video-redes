// twitch.js - Manejo frontend para Twitch

function isValidTwitchUrl(url) {
    return url.includes('twitch.tv') || url.includes('twitch.com');
}

function showTwitchVideo(data, container) {
    console.log("💜 Mostrando video de Twitch:", data);

    if (!data.videoUrl) {
        console.error("❌ No se encontró URL del video de Twitch");
        container.innerHTML = `<div class="error"><h3>No se encontró URL del video de Twitch</h3></div>`;
        return;
    }

    // Enable global download
    // Usamos original_url para forzar descarga HQ por servidor a través de yt-dlp
    const downloadUrl = data.original_url || data.videoUrl;
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(downloadUrl, "twitch_video.mp4");
    }

    // Usar el mismo template unificado
    // data.thumbnail debería venir del extractor
    const cardHtml = renderVideoCard({
        videoUrl: data.videoUrl, // En el caso de Twitch, esto puede ser un m3u8, pero renderVideoCard prioriza thumbnail
        thumbnail: data.thumbnail,
        title: data.title,
        originalUrl: downloadUrl, // Important: Pass original URL for smart download
        duration: data.duration,
        platform: 'twitch',
        views: data.view_count,
        uploader: data.uploader
    });

    container.innerHTML = cardHtml;

    console.log("✅ Video de Twitch mostrado exitosamente");
}
