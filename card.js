function renderVideoCard({ videoUrl = "", thumbnail = "", title = "video", originalUrl = "" }) {
  if (!videoUrl) {
    return `<div class='error'><h3>No se encontró video disponible</h3></div>`;
  }

  if (thumbnail) {
    return `
        <div class="video-thumbnail-container video-card-container">
          <div class="card-video-container">
            <img src="${thumbnail}" alt="${title.replace(/"/g, '&quot;')}"
                 class="card-video-element">
             <!-- Play icon overlay to indicate it is a video -->
             <div class="card-play-icon">▶️</div>
          </div>
        </div>
      `;
  } else {
    // Fallback: Use HTML5 Video to show first frame
    return `
        <div class="video-thumbnail-container video-card-container">
          <div class="card-video-container">
            <video src="${videoUrl}#t=0.01" preload="metadata" muted playsinline controls
                   class="card-video-element">
            </video>
          </div>
        </div>
      `;
  }
}
