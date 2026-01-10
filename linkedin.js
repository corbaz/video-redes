// Funciones específicas para LinkedIn - Updated 2025-06-10
function showLinkedinVideo(data, container) {
    container.innerHTML = "";
    const url = data.videoUrl || "";
    const type = data.type || 'video';

    if (!url) {
        container.innerHTML = `<div class="error"><h3>No se encontró contenido disponible</h3></div>`;
        return;
    }

    // Nombre de archivo dinámico
    const safeTitle = (data.title || "linkedin_content").replace(/[^a-z0-9áéíóúñ_-]/gi, '_').substring(0, 50);

    let filename = `${safeTitle}.mp4`;
    if (type === 'image') filename = `${safeTitle}.jpg`;
    if (type === 'document') filename = `${safeTitle}.pdf`;

    // Enable global download
    if (window.enableGlobalDownload) {
        window.enableGlobalDownload(url, filename);
    }

    // Prepare Click Handler for Preview
    // Use encodeURIComponent for robustness
    const encodedUrl = encodeURIComponent(url);
    const encodedFilename = encodeURIComponent(filename);
    const clickHandler = `onclick="if(window.startSmartDownload) { window.startSmartDownload(decodeURIComponent('${encodedUrl}'), decodeURIComponent('${encodedFilename}')); } else { console.error('SmartDownload not found'); }"`;

    const renderProCard = (contentHtml, badgeLabel, title) => `
        <div class="video-card linkedin-video-card" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
            <div class="video-preview-container linkedin-preview-container">
                <!-- Badge Overlay -->
                <div class="linkedin-badge">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
                    ${badgeLabel}
                </div>
                
                <!-- Main Content -->
                <div class="linkedin-thumb-wrapper">
                    ${contentHtml}
                </div>

                <!-- Title Overlay -->
                <div class="linkedin-title-overlay">
                    <h3 class="linkedin-title">${title}</h3>
                </div>
            </div>
        </div>
    `;

    if (type === 'image') {
        container.innerHTML = renderProCard(
            `<img src="${url}" class="linkedin-thumb-img" alt="LinkedIn Image">`,
            "Imagen",
            data.title || 'Imagen de LinkedIn'
        );
        return;
    }

    if (type === 'document') {
        const hasThumbnail = data.thumbnail && !data.thumbnail.includes('flaticon');
        let content;

        if (hasThumbnail) {
            content = `<img src="${data.thumbnail}" class="linkedin-thumb-img" alt="PDF Cover">`;
        } else {
            content = `
                <div class="linkedin-pdf-bg">
                    <svg viewBox="0 0 24 24" width="60" height="60" stroke="white" stroke-width="1.5" fill="none" class="linkedin-pdf-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                </div>`;
        }

        container.innerHTML = renderProCard(
            content,
            "Documento PDF",
            data.title || 'Documento PDF'
        );
        return;
    }

    // Default Video render
    // IMPORTANT: Pass originalUrl so card.js can set up the click handler for smart download
    const videoCardHTML = renderVideoCard({
        videoUrl: url,
        originalUrl: url, 
        thumbnail: data.thumbnail,
        title: data.title,
        platform: 'linkedin'
    });
    container.innerHTML = videoCardHTML;
}
