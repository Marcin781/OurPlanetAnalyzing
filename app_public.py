from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from planet_engine import source_status

app = FastAPI(title="Dziennik Planety", version="4.0.0")

@app.get("/api/all")
async def all_data():
    return {"updated_at": datetime.now(timezone.utc).isoformat(), "data": await source_status()}

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Dziennik Planety", "version": "4.0.0", "utc": datetime.now(timezone.utc).isoformat()}

MANIFEST = r'''{"name":"Dziennik Planety","short_name":"Planeta","start_url":"/","display":"standalone","background_color":"#071310","theme_color":"#0b211c","description":"Monitoring klimatu, oceanów, lodu, geozagrożeń, bioróżnorodności, pogody kosmicznej i Legnicy."}'''
SW = r'''const CACHE="planet-v4";self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(["/","/manifest.webmanifest","/map.js"]))));self.addEventListener("fetch",e=>{if(e.request.url.includes("/api/"))return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))})'''

@app.get("/manifest.webmanifest")
async def manifest(): return Response(MANIFEST, media_type="application/manifest+json")

@app.get("/sw.js")
async def service_worker(): return Response(SW, media_type="application/javascript")

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML

HTML = r'''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b211c"><link rel="manifest" href="/manifest.webmanifest"><title>Dziennik Planety 4.0</title><style>
:root{font-family:Inter,system-ui,sans-serif;color:#eef8f5;background:#06100e}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% -10%,#1c4a3e,#06100e 55%);min-height:100vh}main{max-width:1250px;margin:auto;padding:18px 16px 60px}.hero,.card{background:#0b1c18e8;border:1px solid #22483f;border-radius:20px;padding:18px}.hero{padding:28px}.eyebrow,.label{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#7fa99f}.hero h1{font-size:clamp(34px,7vw,62px);margin:8px 0}.hero p,.small{color:#a8c8c0;line-height:1.5}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}button{border:0;border-radius:12px;padding:11px 15px;font-weight:750;cursor:pointer;background:#dff8ef;color:#082019}.ghost{background:#17352d;color:#d9eee8}.status{margin-top:12px;color:#82b5a8;font-size:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:18px}.value{font-size:30px;font-weight:800;margin:8px 0}.good{color:#8fe0b9}.warn{color:#ffd078}.bad{color:#ff9d9d}.section{margin-top:18px}.section h2{margin:0 0 12px;font-size:21px}.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #1d3c35}.row:last-child{border:0}.pill{display:inline-block;border:1px solid #315e53;border-radius:999px;padding:4px 8px;font-size:11px}.footer{margin-top:25px;color:#6f9188;font-size:11px;line-height:1.6}.map{height:360px;border-radius:15px;background:#091713;overflow:hidden;display:grid;place-items:center;color:#78978f}
</style></head><body><main><section class="hero"><div class="eyebrow">OurPlanetAnalyzing · Dziennik Planety 4.0</div><h1>Stan Planety</h1><p>Jedno miejsce dla danych klimatycznych, oceanicznych, lodowych, geofizycznych, biologicznych, kosmicznych oraz lokalnych. POMIAR, PROGNOZA i WNIOSEK są rozdzielane.</p><div class="actions"><button onclick="loadData()">Odśwież dane</button><button class="ghost" onclick="installApp()">Zainstaluj aplikację</button></div><div id="status" class="status">Ładowanie…</div></section><section class="grid" id="cards"></section>
<section class="section card"><h2>🌡️ Klimat — NASA + Copernicus</h2><div id="climate"></div><canvas id="chart" class="chart"></canvas></section>
<section class="section card"><h2>🌊 Oceany — wskaźniki</h2><div id="ocean"></div></section>
<section class="section card"><h2>🧊 Lód — NSIDC</h2><div id="ice"></div></section>
<section class="section card"><h2>🔥 Pożary i 🌋 wulkany — NASA EONET</h2><div id="events"></div></section>
<section class="section card"><h2>☀️ Słońce i pogoda kosmiczna — NOAA SWPC</h2><div id="space"></div></section>
<section class="section card"><h2>🧬 Bioróżnorodność — GBIF</h2><div id="bio"></div></section>
<section class="section card"><h2>🍄 Legnica — grzyby</h2><div id="mush"></div></section>
<section class="section card"><h2>🌎 Trzęsienia ziemi — USGS</h2><div id="quakes"></div></section>
<section class="section card"><h2>☄️ Obiekty bliskie Ziemi — NASA/JPL CNEOS</h2><div id="neo"></div></section>
<section class="section card"><h2>🗺️ Mapa świata — zdarzenia na żywo</h2><div class="map">Ładowanie mapy…</div><div class="small">Punkty: USGS trzęsienia ziemi oraz NASA EONET — pożary i wulkany.</div></section>
<section class="section card"><h2>Źródła i status integracji</h2><div id="sources"></div></section><div class="footer">Dane źródłowe nie są zastępowane opinią. Indeks grzybowy jest heurystyką i nie jest prognozą biologiczną. Liczba rekordów GBIF nie oznacza liczebności populacji.</div></main>
<script src="/map.js"></script><script>
let deferredPrompt=null;addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e});const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const v=x=>x==null?'—':esc(x);const box=(a,b)=>`<div class="row"><span>${a}</span><span class="small">${b}</span></div>`;
async function installApp(){if(deferredPrompt){deferredPrompt.prompt();deferredPrompt=null}else alert('Użyj menu przeglądarki → Dodaj do ekranu głównego.')}
async function loadData(){const st=document.getElementById('status');st.textContent='Pobieranie danych…';try{const r=await fetch('/api/all');if(!r.ok)throw Error(r.status);const d=await r.json();render(d.data);st.textContent='Ostatnia aktualizacja: '+new Date(d.updated_at).toLocaleString('pl-PL')}catch(e){st.textContent='Błąd API: '+e}}
function render(x){const t=x.temperature||{},cp=x.copernicus||{},c=x.co2||{},l=x.legnica||{},q=x.earthquakes||{},n=x.neo||{},ev=x.fires_volcanoes||{},sp=x.space_weather||{},b=x.biodiversity||{},o=x.ocean_indicator||{},i=x.ice||{};
document.getElementById('cards').innerHTML=[['NASA temperatura',v(t.latest?.annual_anomaly_c)+' °C'],['Copernicus Climate Pulse',v(cp.latest?.value)+' °C'],['NOAA CO₂',v(c.latest?.co2)+' ppm'],['Legnica grzyby',v(l.mushroom_score)+'/100'],['USGS trzęsienia 24h',v(q.events?.length)],['CNEOS NEO 7 dni',v(n.events?.length)],['EONET zdarzenia',v(ev.events?.length)],['NOAA Kp',v(sp.latest_kp?.kp_index??sp.latest_kp?.kp) ]].map(a=>`<div class="card"><div class="label">${a[0]}</div><div class="value">${a[1]}</div></div>`).join('');
document.getElementById('climate').innerHTML=box('NASA GISS',`${v(t.latest?.annual_anomaly_c)} °C anomalii rocznej; baza 1951–1980`)+box('Copernicus C3S/ECMWF',`${v(cp.latest?.value)} °C; Climate Pulse / ERA5`)+box('NOAA CO₂',`${v(c.latest?.co2)} ppm; r/r ${v(c.year_over_year)} ppm`);draw(cp.rows||[]);
document.getElementById('ocean').innerHTML=box('NOAA AMO',`ostatnie lata: ${v(o.rows?.length)} rekordów`)+box('Interpretacja','AMO nie jest globalną temperaturą oceanu. Do monitoringu SST używamy Copernicus Climate Pulse.')+`<div class="small">Copernicus potwierdza rekordowo wysokie SST w 2026 r.; aplikacja korzysta z dziennej serii ERA5.</div>`;
const ni=i.data||{};document.getElementById('ice').innerHTML=box('Arktyka',`${v(ni.north?.latest?.extent_million_km2)} mln km²`)+box('Antarktyka',`${v(ni.south?.latest?.extent_million_km2)} mln km²`)+`<div class="small">Źródło: NSIDC/NOAA Sea Ice Index v4. Odchylenia porównujemy z klimatologią 1981–2010.</div>`;
document.getElementById('events').innerHTML=box('Pożary',v(ev.counts?.wildfires))+box('Wulkany',v(ev.counts?.volcanoes))+box('Burze',v(ev.counts?.severeStorms));
document.getElementById('space').innerHTML=box('Kp',v(sp.latest_kp?.kp_index??sp.latest_kp?.kp))+box('Cykl słoneczny',v(sp.latest_solar_cycle?.solar_cycle_number??sp.latest_solar_cycle?.cycle));
document.getElementById('bio').innerHTML=box('GBIF Polska — wszystkie rekordy',v(b.poland_occurrences_total))+box('GBIF Polska — bieżący rok',v(b.poland_occurrences_current_year))+`<div class="small">To wskaźnik aktywności obserwacyjnej, nie bezpośredni indeks liczebności gatunków.</div>`;
const h=l.history||{};document.getElementById('mush').innerHTML=`<div class="value ${l.mushroom_score>=70?'good':l.mushroom_score>=45?'warn':'bad'}">${v(l.mushroom_score)}/100</div>`+box('Opad 7 dni',v(h.rain_7d_mm)+' mm')+box('Opad 14 dni',v(h.rain_14d_mm)+' mm')+box('Śr. temperatura 7 dni',v(h.avg_temp_7d_c)+' °C')+box('Śr. wilgotność',v(h.avg_humidity_7d_pct)+'%')+box('Wilgotność gleby',v(h.avg_soil_moisture))+`<div class="small">POMIAR + PROGNOZA → własna heurystyka warunków grzybowych.</div>`;
document.getElementById('quakes').innerHTML=(q.events||[]).slice(0,10).map(e=>box('M'+v(e.magnitude)+' · '+v(e.place),v(e.depth_km)+' km')).join('')||'Brak danych';document.getElementById('neo').innerHTML=(n.events||[]).slice(0,10).map(e=>box(v(e.des),v(e.cd))).join('')||'Brak podejść spełniających filtr';document.getElementById('sources').innerHTML=Object.entries(x).map(([k,z])=>box(k,`<span class="pill ${z.status==='ok'?'good':'bad'}">${v(z.status)}</span>`)).join('')}
function draw(rows){const c=document.getElementById('chart'),ctx=c.getContext('2d'),w=c.clientWidth,h=c.clientHeight,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;ctx.scale(d,d);ctx.clearRect(0,0,w,h);const a=rows.slice(-90),ys=a.map(z=>z.value).filter(Number.isFinite);if(ys.length<2)return;const mn=Math.min(...ys),mx=Math.max(...ys);ctx.beginPath();a.forEach((p,j)=>{if(!Number.isFinite(p.value))return;const xx=10+j*(w-20)/Math.max(1,a.length-1),yy=h-10-(p.value-mn)/(mx-mn||1)*(h-20);j?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy)});ctx.strokeStyle='#9be3c4';ctx.lineWidth=2.5;ctx.stroke();ctx.fillStyle='#9be3c4';ctx.font='12px system-ui';ctx.fillText(mx.toFixed(2)+' °C',10,14);ctx.fillText(mn.toFixed(2)+' °C',10,h-3)}
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js');loadData();setInterval(loadData,600000);
</script></body></html>'''
