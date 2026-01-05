// Tarjeta profesional reutilizable para mostrar un video
function renderVideoCard({ videoUrl = "", thumbnail = "", title = "video", originalUrl = "" }) {
  if (!videoUrl) {
    return `<div class='error'><h3>No se encontró video disponible</h3></div>`;
  }

  // Si hay thumbnail, usamos poster, si no, dejamos que el video intente cargar el primer frame
  const posterAttr = thumbnail ? `poster="${thumbnail.replace(/"/g, '&quot;')}"` : "";

  return `
    <div class="video-thumbnail-container video-card-container">
      <div style="position:relative; width:100%; padding-bottom:177.78%; background:#000; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3); cursor: pointer;"
           onclick="showVideoModal('${videoUrl.replace(/'/g, "\\'")}', '${title.replace(/'/g, "\\'")}', '${originalUrl ? originalUrl.replace(/'/g, "\\'") : ""}')">
        <video src="${videoUrl}" ${posterAttr}
               style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; border-radius:12px; background:#000;"
               muted loop playsinline preload="metadata" tabindex="-1"></video>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:40px; height:40px; background:rgba(255,255,255,0.2); border-radius:50%; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(4px); border:2px solid rgba(255,255,255,0.3); transition:all 0.3s; pointer-events:none;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="#fff" style="margin-left:2px;">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>
    </div>
  `;
}
