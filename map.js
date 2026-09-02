// Interactive event-map helper for Dziennik Planety.
(function () {
  function buildEventPoints(data) {
    const points = [];
    for (const event of (data?.earthquakes?.events || [])) {
      const lat = Number(event.latitude ?? event.geometry?.coordinates?.[1]);
      const lon = Number(event.longitude ?? event.geometry?.coordinates?.[0]);
      if (Number.isFinite(lat) && Number.isFinite(lon)) points.push({lat, lon, type:'earthquake', title:event.place || 'USGS earthquake', value:event.magnitude});
    }
    for (const event of (data?.fires_volcanoes?.events || [])) {
      const coords = event.geometry;
      const lon = Number(Array.isArray(coords) ? coords[0] : NaN);
      const lat = Number(Array.isArray(coords) ? coords[1] : NaN);
      if (Number.isFinite(lat) && Number.isFinite(lon)) points.push({lat, lon, type:(event.categories||[]).includes('volcanoes')?'volcano':'wildfire', title:event.title || 'NASA EONET event'});
    }
    return points;
  }

  function loadLeaflet() {
    if (window.L) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const css = document.createElement('link'); css.rel='stylesheet'; css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'; document.head.appendChild(css);
      const script = document.createElement('script'); script.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'; script.onload=resolve; script.onerror=reject; document.head.appendChild(script);
    });
  }

  async function init() {
    const placeholder = document.querySelector('.map');
    if (!placeholder || placeholder.dataset.mapReady) return;
    placeholder.dataset.mapReady='1'; placeholder.id='worldMap'; placeholder.textContent='Ładowanie mapy…';
    try {
      await loadLeaflet();
      placeholder.textContent='';
      const map = L.map('worldMap').setView([20,0],2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:7,attribution:'© OpenStreetMap contributors'}).addTo(map);
      const layer = L.layerGroup().addTo(map);
      const r = await fetch('/api/all'); const payload = await r.json();
      for (const p of buildEventPoints(payload.data)) {
        const label = p.type==='earthquake' ? `🌎 M${p.value ?? '—'} · ${p.title}` : (p.type==='volcano' ? `🌋 ${p.title}` : `🔥 ${p.title}`);
        L.circleMarker([p.lat,p.lon],{radius:p.type==='earthquake'?Math.max(4,Math.min(10,Number(p.value||4))):6}).addTo(layer).bindPopup(label);
      }
    } catch (err) { placeholder.textContent='Mapa niedostępna — dane zdarzeń pozostają dostępne w tabelach.'; console.warn('Map error',err); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
