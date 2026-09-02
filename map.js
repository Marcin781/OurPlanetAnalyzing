// Map removed from the mobile dashboard to reduce network, CPU and data usage.
(function () {
  function removeMap() {
    const headings = document.querySelectorAll('.section.card h2');
    for (const h of headings) {
      if (h.textContent.includes('Mapa świata')) {
        const section = h.closest('.section.card');
        if (section) section.remove();
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', removeMap);
  else removeMap();
})();
