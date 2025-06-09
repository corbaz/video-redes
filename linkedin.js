// Funciones específicas para LinkedIn
function showLinkedinVideo(data, container) {
    // Limpiar el contenedor
    container.innerHTML = '';

    // Extraer información del video
    const formats = data.video_formats || [];
    if (formats.length === 0) {
        container.innerHTML = `<div class="error"><h3>No se encontraron videos disponibles</h3></div>`;
        return;
    }
    
    // Tomar el primer formato de mejor calidad
    const format = formats[0];
    const videoUrl = format.url || '';
    const thumbnail = data.thumbnail || '';
    
    // Extraer título y usuario del título de LinkedIn
    let title = data.title || '';
    let uploader = '';
    
    // Intentar extraer el usuario del título (formato: "Título | Usuario | X comentarios")
    const titleParts = title.split('|').map(part => part.trim());
    if (titleParts.length >= 2) {
        title = titleParts[0];
        uploader = titleParts[1];
    }
    
    // Crear la tarjeta de video usando la función renderVideoCard
    const videoCardHTML = renderVideoCard({
        title: title,
        uploader: uploader,
        videoUrl: videoUrl,
        thumbnail: thumbnail
    });
    
    // Agregar la tarjeta al contenedor
    container.innerHTML = videoCardHTML;
}

function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}
