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

    const renderProCard = (contentHtml, badgeLabel, title) => `
        <div class="video-card" style="border: none; background: transparent; box-shadow: none; display: flex; justify-content: center;">
            <div class="video-preview-container" style="position: relative; width: 200px; aspect-ratio: 9/16; border-radius: 12px; overflow: hidden; background: #0f172a; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <!-- Badge Overlay -->
                <div style="position: absolute; top: 12px; left: 12px; z-index: 10; background: rgba(0, 119, 181, 0.9); color: white; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; backdrop-filter: blur(4px); display: flex; align-items: center; gap: 4px;">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
                    ${badgeLabel}
                </div>
                
                <!-- Main Content -->
                <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #000;">
                    ${contentHtml}
                </div>

                <!-- Title Overlay -->
                <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 15px; padding-top: 40px; background: linear-gradient(to top, rgba(0,0,0,0.9), transparent); z-index: 10;">
                    <h3 style="color: white; margin: 0; font-size: 0.95rem; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.5); line-height: 1.3; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${title}</h3>
                </div>
            </div>
        </div>
    `;

    if (type === 'image') {
        container.innerHTML = renderProCard(
            `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover;" alt="LinkedIn Image">`,
            "Imagen",
            data.title || 'Imagen de LinkedIn'
        );
        return;
    }

    if (type === 'document') {
        const hasThumbnail = data.thumbnail && !data.thumbnail.includes('flaticon');
        let content;

        if (hasThumbnail) {
            content = `<img src="${data.thumbnail}" style="width: 100%; height: 100%; object-fit: cover;" alt="PDF Cover">`;
        } else {
            content = `
                <div style="width: 100%; height: 100%; background: radial-gradient(circle at center, #3b82f6, #1e3a8a); display: flex; align-items: center; justify-content: center;">
                    <svg viewBox="0 0 24 24" width="60" height="60" stroke="white" stroke-width="1.5" fill="none" style="opacity: 0.7"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
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
    const videoCardHTML = renderVideoCard({
        videoUrl: url,
        thumbnail: data.thumbnail,
        title: data.title,
        platform: 'linkedin'
    });
    container.innerHTML = videoCardHTML;
}
