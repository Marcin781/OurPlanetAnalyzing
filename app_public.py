from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from planet_engine import source_status

app = FastAPI(title="Dziennik Planety", version="3.0.0")


@app.get("/api/all")
async def all_data():
    return {"updated_at": datetime.now(timezone.utc).isoformat(), "data": await source_status()}


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Dziennik Planety", "version": "3.0.0", "utc": datetime.now(timezone.utc).isoformat()}


@app.get("/manifest.webmanifest")
async def manifest():
    return Response(MANIFEST, media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker():
    return Response(SW, media_type="application/javascript")


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML


MANIFEST = r'''{"name":"Dziennik Planety","short_name":"Planeta","start_url":"/","display":"standalone","background_color":"#071310","theme_color":"#0b211c","description":"Publiczny monitoring klimatu, Ziemi, pogody kosmicznej i Legnicy."}'''

SW = r'''const CACHE="planet-v3"; self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(["/","/manifest.webmanifest"])))); self.addEventListener("fetch",e=>{if(e.request.url.includes("/api/"))return; e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))})'''

HTML = r'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b211c"><link rel="manifest" href="/manifest.webmanifest"><title>Dziennik Planety 3.0</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#eef8f5;background:#06100e}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% -10%,#1c4a3e,#06100e 55%);min-height:100vh}main{max-width:1200px;margin:auto;padding:18px 16px 60px}.hero{padding:28px;border:1px solid #2b6254;border-radius:26px;background:#0b211ddd;box-shadow:0 20px 80px #0008}.eyebrow{font-size:11px;letter-spacing:.16em;color:#8ab8ac;text-transform:uppercase}.hero h1{font-size:clamp(34px,7vw,64px);margin:8px 0}.hero p{color:#b3d0c8;max-width:720px;line-height:1.55}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}button{border:0;border-radius:12px;padding:11px 15px;font-weight:750;cursor:pointer;background:#dff8ef;color:#082019}.ghost{background:#17352d;color:#d9eee8}.status{margin-top:12px;color:#82b5a8;font-size:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:18px}.card{background:#0b1c18e8;border:1px solid #22483f;border-radius:18px;padding:18px}.label{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#7fa99f}.value{font-size:30px;font-weight:800;margin:9px 0}.small{font-size:13px;line-height:1.5;color:#a8c8c0}.good{color:#8fe0b9}.warn{color:#ffd078}.bad{color:#ff9d9d}.section{margin-top:18px}.section h2{margin:0 0 12px;font-size:22px}.chart{height:190px;width:100%;display:block}.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #1d3c35}.row:last-child{border-bottom:0}.pill{display:inline-block;border:1px solid #315e53;border-radius:999px;padding:4px 8px;font-size:11px}.footer{margin-top:25px;color:#6f9188;font-size:11px;line-height:1.6}.legend{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.map{height:260px;border-radius:16px;background:#091713;display:grid;place-items:center;color:#78978f}.hide{display:none}
</style></head><body><main>
<section class="hero"><div class="eyebrow">OurPlanetAnalyzing · Dziennik Planety 3.0</div><h1>Stan Planety</h1><p>Jedno miejsce dla danych klimatycznych, geofizycznych, kosmicznych i lokalnych. Dane źródłowe są oddzielone od prognoz i własnych wniosków.</p><div class="actions"><button onclick="loadData()">Odśwież dane</button><button class="ghost" onclick="installApp()">Zainstaluj aplikację</button></div><div id="status" class="status">Ładowanie…</div></section>
<section class="grid" id="cards"></section>
<section class="section card"><h2>CO₂ — NOAA</h2><canvas id="co2chart" class="chart"></canvas><div id="co2meta" class="small"></div></section>
<section class="section card"><h2>Legnica — grzyby</h2><div id="mush"></div></section>
<section class="section card"><h2>🌎 Trzęsienia ziemi — USGS</h2><div id="quakes"></div></section>
<section class="section card"><h2>☄️ Obiekty bliskie Ziemi — NASA/JPL CNEOS</h2><div id="neo"></div></section>
<section class="section card"><h2>Mapa świata</h2><div class="map">Warstwa mapowa jest przygotowana jako kolejny moduł. Dane geolokalizacyjne pozostają po stronie serwera.</div></section>
<section class="section card"><h2>Źródła i status integracji</h2><div id="sources"></div></section>
<div class="footer">POMIAR = dane obserwacyjne · PROGNOZA = model/przewidywanie · ANOMALIA = odchylenie od normy · WNIOSEK = interpretacja. Indeks grzybowy jest heurystyką i nie jest prognozą biologiczną.</div>
</main>
<script>
let deferredPrompt=null; window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e});
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function val(x){return x===null||x===undefined?'—':esc(x)}
async function installApp(){if(deferredPrompt){deferredPrompt.prompt();deferredPrompt=null}else{alert('Jeśli przeglądarka obsługuje PWA, użyj menu przeglądarki i wybierz „Dodaj do ekranu głównego”.')}}
async function loadData(){document.getElementById('status').textContent='Pobieranie danych ze źródeł…';try{const r=await fetch('/api/all');const d=await r.json();render(d);document.getElementById('status').textContent='Ostatnia aktualizacja: '+new Date(d.updated_at).toLocaleString('pl-PL')}catch(e){document.getElementById('status').textContent='Błąd pobierania danych: '+e}}
function render(d){const x=d.data||{}, t=x.temperature||{}, c=x.co2||{}, l=x.legnica||{}, q=x.earthquakes||{}, n=x.neo||{};document.getElementById('cards').innerHTML=`<div class="card"><div class="label">Globalna temperatura</div><div class="value">${val(t.latest?.annual_anomaly_c)} °C</div><div class="small">NASA GISS · anomalia roczna. Najnowszy dostępny rekord.</div></div><div class="card"><div class="label">CO₂</div><div class="value">${val(c.latest?.co2)} ppm</div><div class="small">NOAA GML / Mauna Loa · r/r: ${val(c.year_over_year)} ppm</div></div><div class="card"><div class="label">Trzęsienia · 24 h</div><div class="value">${val(q.events?.length)}</div><div class="small">USGS · bieżący strumień dobowy</div></div><div class="card"><div class="label">NEO · 7 dni</div><div class="value">${val(n.events?.length)}</div><div class="small">NASA/JPL CNEOS · podejścia ≤ 0,05 AU</div></div>`;document.getElementById('co2meta').innerHTML=`Ostatni pomiar: <b>${val(c.latest?.co2)} ppm</b>. Źródło: NOAA GML. <span class="pill">POMIAR</span>`;drawCO2(c.rows||[]);const h=l.history||{};const score=l.mushroom_score??0;document.getElementById('mush').innerHTML=`<div class="value ${score>=70?'good':score>=45?'warn':'bad'}">${val(score)}/100</div><div class="small">7 dni: ${val(h.rain_7d_mm)} mm opadu · 14 dni: ${val(h.rain_14d_mm)} mm · średnia temperatura: ${val(h.avg_temp_7d_c)} °C · wilgotność: ${val(h.avg_humidity_7d_pct)}% · wilgotność gleby: ${val(h.avg_soil_moisture)}.</div><div class="legend"><span class="pill">POMIAR</span><span class="pill">PROGNOZA</span><span class="pill">WNIOSKI: heurystyka</span></div>`;document.getElementById('quakes').innerHTML=(q.events||[]).slice(0,12).map(e=>`<div class="row"><span>M${val(e.magnitude)} · ${val(e.place)}</span><span class="small">${e.depth_km?val(e.depth_km)+' km':''}</span></div>`).join('')||'<div class="small">Brak danych.</div>';document.getElementById('neo').innerHTML=(n.events||[]).slice(0,10).map(e=>`<div class="row"><span>${val(e.des)}</span><span class="small">${val(e.cd)}</span></div>`).join('')||'<div class="small">Brak podejść spełniających filtr.</div>';document.getElementById('sources').innerHTML=Object.entries(x).map(([k,v])=>`<div class="row"><span>${esc(k)}</span><span class="pill ${v.status==='ok'?'good':'bad'}">${val(v.status)}</span></div>`).join('')}
function drawCO2(rows){const c=document.getElementById('co2chart'),ctx=c.getContext('2d'),dpr=devicePixelRatio||1,w=c.clientWidth,h=c.clientHeight;c.width=w*dpr;c.height=h*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);const a=rows.slice(-36),ys=a.map(x=>x.co2).filter(Number.isFinite);if(!ys.length)return;const min=Math.min(...ys),max=Math.max(...ys),pad=12;ctx.beginPath();a.forEach((p,i)=>{const x=pad+i*(w-2*pad)/Math.max(1,a.length-1),y=h-pad-(p.co2-min)/(max-min||1)*(h-2*pad);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle='#9be3c4';ctx.lineWidth=2.5;ctx.stroke();ctx.fillStyle='#9be3c4';ctx.font='12px system-ui';ctx.fillText(Math.round(max*100)/100+' ppm',pad,14);ctx.fillText(Math.round(min*100)/100+' ppm',pad,h-3)}
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js');loadData();setInterval(loadData,600000);
</script></body></html>'''
