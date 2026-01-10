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
  const playIconHtml = (type === 'image') ? '' : `
    <button class="ytp-large-play-button ytp-button ytp-large-play-button-red-bg" aria-label="Reproducir" title="Reproducir" style="pointer-events: none;">
      <svg height="100%" version="1.1" viewBox="0 0 68 48" width="100%">
        <path class="ytp-large-play-button-bg" d="M66.52,7.74c-0.78-2.93-2.49-5.41-5.42-6.19C55.79,.13,34,0,34,0S12.21,.13,6.9,1.55 C3.97,2.33,2.27,4.81,1.48,7.74C0.06,13.05,0,24,0,24s0.06,10.95,1.48,16.26c0.78,2.93,2.49,5.41,5.42,6.19 C12.21,47.87,34,48,34,48s21.79-0.13,27.1-1.55c2.93-0.78,4.64-3.26,5.42-6.19C67.94,34.95,68,24,68,24S67.94,13.05,66.52,7.74z" fill="#f03"></path>
        <path d="M 45,24 27,14 27,34" fill="#fff"></path>
      </svg>
    </button>`;

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
             ${playIconHtml}
          </div>
        </div>
      `;
  }
}
