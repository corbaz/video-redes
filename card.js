function renderVideoCard({ videoUrl = "", thumbnail = "", title = "video", originalUrl = "" }) {
  if (!videoUrl) {
    return `<div class='error'><h3>No se encontró video disponible</h3></div>`;
  }

  if (thumbnail) {
    return `
        <div class="video-thumbnail-container video-card-container">
          <div style="position:relative; width:100%; padding-bottom:177.78%; background:#000; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <img src="${thumbnail}" alt="${title.replace(/"/g, '&quot;')}"
                 style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; border-radius:12px;">
             <!-- Play icon overlay to indicate it is a video -->
             <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 3rem; opacity: 0.8;">▶️</div>
          </div>
        </div>
      `;
  } else {
    // Fallback: Use HTML5 Video to show first frame
    return `
        <div class="video-thumbnail-container video-card-container">
          <div style="position:relative; width:100%; padding-bottom:177.78%; background:#000; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <video src="${videoUrl}#t=0.01" preload="metadata" muted playsinline controls
                   style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; border-radius:12px;">
            </video>
          </div>
        </div>
      `;
  }
}
