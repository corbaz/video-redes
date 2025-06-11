// Funciones específicas para LinkedIn - Updated 2025-06-10
function showLinkedinVideo(data, container) {
    console.log("LinkedIn showLinkedinVideo called with:", data);
    container.innerHTML = "";
    const videoUrl = data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    // Renderizar la tarjeta con preview igual que Instagram
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
    });
    container.innerHTML = videoCardHTML;
}

function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
