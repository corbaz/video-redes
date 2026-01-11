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

    const linkedinIcon = `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#0077B5" xmlns="http://www.w3.org/2000/svg"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" /></svg>`;
    
    const iconOverlay = `
        <div class="platform-icon-overlay" aria-hidden="true" style="pointer-events: none;">
            ${linkedinIcon}
        </div>`;

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
                    ${iconOverlay}
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

    if (type === 'gallery') {
        const images = data.images || [];
        const count = images.length;
        const firstImage = images[0] || '';
        
        // JSON stringify the array of URLs to pass as the "url" parameter
        const imagesJson = JSON.stringify(images);
        const zipFilename = `${safeTitle}.zip`;
        
        // Override the default click handler for this card to pass the JSON string
        const encodedJson = encodeURIComponent(imagesJson);
        const encodedZipName = encodeURIComponent(zipFilename);
        const galleryClickHandler = `onclick="if(window.startSmartDownload) { window.startSmartDownload(decodeURIComponent('${encodedJson}'), decodeURIComponent('${encodedZipName}')); } else { console.error('SmartDownload not found'); }"`;

        const galleryContent = `
            <div class="linkedin-gallery-wrapper" style="position: relative;">
                <img src="${firstImage}" class="linkedin-thumb-img" alt="Gallery Cover">
                <div class="gallery-count-badge" style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; display: flex; align-items: center; gap: 4px;">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="white"><path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z"/></svg>
                    <span>${count} Imágenes</span>
                </div>
                ${iconOverlay}
            </div>`;

        // We reconstruct the card manually because renderProCard uses the outer scope 'clickHandler' 
        // which points to single URL. We need 'galleryClickHandler'.
        
        container.innerHTML = `
        <div class="video-card linkedin-video-card" style="cursor: pointer;" ${galleryClickHandler} title="Descargar ${count} imágenes (ZIP)">
            <div class="video-preview-container linkedin-preview-container">
                <div class="linkedin-badge">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z"/></svg>
                    Galería
                </div>
                
                ${galleryContent}

                <div class="linkedin-title-overlay">
                    <h3 class="linkedin-title">${data.title || 'Galería de LinkedIn'}</h3>
                </div>
            </div>
        </div>
        `;
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
        filename: filename,
        platform: 'linkedin'
    });
    container.innerHTML = videoCardHTML;
}
