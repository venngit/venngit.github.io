(function(){
  // Highlight footer link matching current page by adding class 'footer-current'
  try {
    const links = document.querySelectorAll('.footer-links a');
    if (!links || links.length === 0) return;
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    // Treat root path as index.html
    const candidates = [currentPath, '/' + currentPath, '', window.location.pathname];
    links.forEach(a => {
      try {
        const href = a.getAttribute('href') || '';
        // Normalize href by removing any query/hash
        const hrefPath = href.split('?')[0].split('#')[0].split('/').pop();
        if (!hrefPath) return;
        if (hrefPath === currentPath || (currentPath === '' && hrefPath.toLowerCase() === 'index.html')) {
          a.classList.add('footer-current');
        }
      } catch (e) { /* ignore */ }
    });
  } catch (e) { console.error(e); }
})();
