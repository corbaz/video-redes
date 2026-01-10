function renderVideoCard({ videoUrl = "", thumbnail = "", title = "video", originalUrl = "", filename = "", type = "video", platform = "" }) {
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

  // Platform Icons Definitions
  const platformIcons = {
    'instagram': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="url(#instagram-gradient)" xmlns="http://www.w3.org/2000/svg"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" /></svg>`,
    'linkedin': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#0077B5" xmlns="http://www.w3.org/2000/svg"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" /></svg>`,
    'x': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#ffffff" xmlns="http://www.w3.org/2000/svg"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>`,
    'twitter': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#ffffff" xmlns="http://www.w3.org/2000/svg"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>`,
    'tiktok': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#ff0050" xmlns="http://www.w3.org/2000/svg"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.49-3.35-3.98-5.6-.48-2.21-.08-4.59 1.12-6.52 1.54-2.48 4.25-4.12 7.15-4.3.01 1.52.01 3.03.02 4.14-1.68.07-3.3.74-4.52 1.86-1.2 1.09-1.87 2.71-1.82 4.31.05 1.62.96 3.1 2.38 3.96 1.07.65 2.35.84 3.56.57 1.25-.26 2.35-1.05 3.02-2.14.73-1.19.78-2.61.78-3.97v-6.91c0-1.84.05-3.67.05-5.52h-4.09V.02z" /></svg>`,
    'facebook': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#1877f2" xmlns="http://www.w3.org/2000/svg"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" /></svg>`,
    'youtube': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#ff0000" xmlns="http://www.w3.org/2000/svg"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>`,
    'twitch': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#9146FF" xmlns="http://www.w3.org/2000/svg"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z" /></svg>`,
    'pinterest': `<svg viewBox="0 0 24 24" class="platform-icon-svg" fill="#BD081C" xmlns="http://www.w3.org/2000/svg"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.399.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.951-7.252 4.173 0 7.41 2.967 7.41 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.367 18.62 0 12.017 0z" /></svg>`
  };

  // Select icon based on platform (normalized to lowercase)
  const platformKey = (platform || '').toLowerCase();
  const selectedIcon = platformIcons[platformKey] || platformIcons['youtube']; // Default to YouTube or maybe a generic play? User asked for specific network icon. If unknown, maybe generic play is better, but let's stick to what we have.

  // If no specific platform icon found and it's not youtube, maybe fallback to generic play or just show nothing? 
  // But usually platform will be one of the known ones.
  // Let's use the selectedIcon if found, otherwise keep the youtube-style play button as a fallback or empty.
  // Actually, user wants "icono de la red de donde proviene".
  
  const iconHtml = `
    <div class="platform-icon-overlay" aria-hidden="true" style="pointer-events: none;">
        ${selectedIcon}
    </div>`;

  if (thumbnail) {
    return `
        <div class="video-thumbnail-container video-card-container" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
          <div class="card-video-container">
            <img src="${thumbnail}" alt="${safeTitle}"
                 class="card-video-element"
                 onerror="if (this.src.includes('maxresdefault')) { this.src = this.src.replace('maxresdefault.jpg', 'hqdefault.jpg'); } else { this.src = 'https://via.placeholder.com/800x450/000000/FFFFFF?text=No+Thumbnail'; }">
            ${iconHtml}
          </div>
        </div>
      `;
  } else {
    // Fallback: Use HTML5 Video
    return `
        <div class="video-thumbnail-container video-card-container" style="cursor: pointer;" ${clickHandler} title="Clic para descargar">
          <div class="card-video-container">
            <video src="${safeVideoUrl}#t=0.01" preload="metadata" muted playsinline
                   class="card-video-element" style="pointer-events: none;">
            </video>
             ${iconHtml}
          </div>
        </div>
      `;
  }
}
