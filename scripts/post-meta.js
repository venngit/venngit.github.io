// Shared post meta loader
(function(){
  function formatDate(dateString){
    if(!dateString) return '';
    const parts = dateString.split('-');
    if(parts.length !== 3) return dateString;
    const day = parts[0];
    const month = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`).toLocaleString('en-US',{month:'short'});
    const year = parts[2];
    return `${day} ${month} ${year}`;
  }

  function populate(post){
    try{
      const titleEl = document.getElementById('post-title');
      if(titleEl && post.title) titleEl.textContent = post.title;
      const dateEl = document.getElementById('post-date');
      if(dateEl && post.published) dateEl.textContent = 'Published on ' + formatDate(post.published);

      const imgEl = document.getElementById('post-image');
      if(imgEl && post.image){
        const hero = post.hero || post.image;
        const thumb = post.thumb || post.image;
        imgEl.src = hero || thumb || post.image;
        imgEl.alt = post.title || imgEl.alt || '';
        const srcset = [];
        if(post.hero) srcset.push(`${post.hero} 1600w`);
        if(post.thumb) srcset.push(`${post.thumb} 800w`);
        if(post.image) srcset.push(`${post.image} 400w`);
        if(srcset.length) imgEl.srcset = srcset.join(', ');
        if(!imgEl.sizes) imgEl.sizes = '(min-width:1600px) 1600px, (min-width:1000px) 1000px, 100vw';
      }

      // If post has map and a global initMap exists, show the map container then init
      if(post.hasMap){
        const mapEl = document.getElementById('basicMap');
        if(mapEl) mapEl.style.display = 'block';
        if(typeof window.initMap === 'function' && post.mapCoordinates){
          // call initMap with [lon,lat]
          try{ window.initMap([post.mapCoordinates.lon, post.mapCoordinates.lat]); }catch(e){}
        }
      }

      // If JSON contains content fields and element exists, populate only if empty
      if(post.content){
        const contentEl = document.getElementById('post-content');
        if(contentEl && !contentEl.textContent.trim()) contentEl.textContent = post.content;
      }
    }catch(e){ console.error('post-meta populate error', e); }
  }

  // Auto-run
  (function(){
    // Use decoded filename so URLs with spaces (%20) match entries in blog-posts.json
    const filename = decodeURIComponent(window.location.pathname.split('/').pop());
    fetch('/posts/blog-posts.json')
      .then(r => r.json())
      .then(data => {
        if(!data || !Array.isArray(data.posts)) return;
        const post = data.posts.find(p => p.link && p.link.endsWith(filename)) || data.posts.find(p => p.title && p.title.replace(/\s+/g,'-').toLowerCase().includes(filename.replace(/\.[^.]+$/,'')));
        if(post) populate(post);
      }).catch(()=>{});
  })();
})();
