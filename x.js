// Funciones específicas para X/Twitter - COPIANDO EXACTAMENTE LinkedIn
function showXVideo(data, container) {
    container.innerHTML = "";
    const videoUrl = data.videoUrl || "";
    if (!videoUrl) {
        container.innerHTML = `<div class="error"><h3>No se encontró video disponible</h3></div>`;
        return;
    }
    // Renderizar la tarjeta con preview igual que LinkedIn
    const videoCardHTML = renderVideoCard({
        videoUrl: videoUrl,
    });
    container.innerHTML = videoCardHTML;
}
