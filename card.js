function renderVideoCard({ videoUrl = "", thumbnail = "", title = "video", originalUrl = "", filename = "", type = "video" }) {
  if (!videoUrl) {
    return `<div class='error'><h3>No se encontró video disponible</h3></div>`;
  }

  // Determine filename
  const finalFilename = filename || `${title}.mp4`;

  // Escape attributes for HTML display (alt, src)
  // Replace newlines and backslashes to prevent breaking JS string
  const safeTitle = title.replace(/\\/g, '\\\\').replace(/\n/g, ' ').replace(/\r/g, '').replace(/"/g, '&quot;').replace(/'/g, "\\'");
  const safeVideoUrl = videoUrl.replace(/"/g, '&quot;').replace(/'/g, "\\'");

  // Use encodeURIComponent for the onclick handler parameters to avoid ALL quoting issues
  const encodedUrl = encodeURIComponent(originalUrl || videoUrl);
  const encodedFilename = encodeURIComponent(finalFilename);

  // Add onclick handler to trigger smart download
  // We use decodeURIComponent inside the onclick to restore the original values before passing to the function
  const clickHandler = `onclick="if(window.startSmartDownload) { window.startSmartDownload(decodeURIComponent('${encodedUrl}'), decodeURIComponent('${encodedFilename}')); } else { console.error('SmartDownload not found'); }"`;

  // Render Play Icon only if it is NOT an image
  const playIconHtml = (type === 'image') ? '' : '<div class="card-play-icon" style="pointer-events: none;">▶️</div>';

  if (thumbnail) {
    return `
        <div class="video-thumbnail-container video-card-container" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
          <div class="card-video-container">
            <img src="${thumbnail}" alt="${safeTitle}"
                 class="card-video-element">
            ${playIconHtml}
          </div>
        </div>
      `;
  } else {
    // Fallback: Use HTML5 Video to show first frame
    // Note: Video element clicks might play the video instead of downloading. 
    // We wrap it in a container that handles the click, but controls on video might interfere.
    // For consistency with user request "preview encontrada que haga como la funcion del boton descargar", 
    // we should probably allow playing if controls are present, or maybe overlay a download trigger.
    // However, usually "preview" implies the image card. If it's a video tag, it's already playable.
    // User said "preview encontrada", usually meaning the result card.
    // Let's add the click handler to the container.
    return `
        <div class="video-thumbnail-container video-card-container" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
          <div class="card-video-container">
            <video src="${safeVideoUrl}#t=0.01" preload="metadata" muted playsinline
                   class="card-video-element" style="pointer-events: none;">
            </video>
             <div class="card-play-icon" style="pointer-events: none;">▶️</div>
          </div>
        </div>
      `;
  }
}
