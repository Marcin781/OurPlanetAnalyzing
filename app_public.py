import csv
import io
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Dziennik Planety", version="2.0.0")

LEGNICA_LAT = 51.207, 16.161


async def get_json(url: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


@app.get("/api/earthquakes")
async def earthquakes():
    data = await get_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
    rows = []
    for f in data.get("features", [])[:30]:
        p = f.get("properties", {})
        rows.append({"place": p.get("place"), "magnitude": p.get("mag"), "time": p.get("time"), "url": p.get("url")})
    return {"source": "USGS", "updated": datetime.now(timezone.utc).isoformat(), "count": len(rows), "events": rows}


@app.get("/api/co2")
async def co2():
    url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
    rows = []
    for row in csv.reader(io.StringIO(r.text)):
        if not row or row[0].startswith("#") or row[0] == "year":
            continue
        try:
            rows.append({"year": int(row[0]), "month": int(row[1]), "co2": float(row[4])})
        except (ValueError, IndexError):
            continue
    rows = rows[-24:]
    return {"source": "NOAA GML / Mauna Loa", "unit": "ppm", "rows": rows, "latest": rows[-1] if rows else None}


@app.get("/api/legnica")
async def legnica():
    lat, lon = LEGNICA_LAT
    data = await get_json(
        "https://api.open-meteo.com/v1/forecast",
        {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,precipitation,rain", "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_0_to_7cm", "past_days": 14, "forecast_days": 7, "timezone": "Europe/Warsaw"},
    )
    h = data.get("hourly", {})
    temps = h.get("temperature_2m", [])
    rain = h.get("precipitation", [])
    humidity = h.get("relative_humidity_2m", [])
    recent = list(zip(temps, rain, humidity))[-168:]
    rain_7d = round(sum(float(x[1] or 0) for x in recent), 1) if recent else 0
    avg_temp = round(sum(float(x[0]) for x in recent) / len(recent), 1) if recent else None
    avg_hum = round(sum(float(x[2]) for x in recent) / len(recent), 1) if recent else None
    # Heuristic only: useful for comparison, not a biological forecast.
    score = 0
    score += min(40, rain_7d * 2)
    if avg_temp is not None and 12 <= avg_temp <= 24:
        score += 30
    if avg_hum is not None and avg_hum >= 75:
        score += 30
    score = max(0, min(100, round(score)))
    return {"source": "Open-Meteo", "location": {"lat": lat, "lon": lon}, "current": data.get("current"), "rain_7d_mm": rain_7d, "avg_temp_7d_c": avg_temp, "avg_humidity_7d_pct": avg_hum, "mushroom_score": score, "mushroom_note": "Wskaźnik heurystyczny oparty na opadach, temperaturze i wilgotności; nie jest prognozą biologiczną."}


@app.get("/api/summary")
async def summary():
    out = {"updated_at": datetime.now(timezone.utc).isoformat(), "modules": ["CO₂", "Trzęsienia ziemi", "Legnica — grzyby"]}
    for key, fn in (("co2", co2), ("earthquakes", earthquakes), ("legnica", legnica)):
        try:
            out[key] = await fn()
        except Exception as exc:
            out[key] = {"error": str(exc)}
    return out


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML


HTML = r'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dziennik Planety</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:#edf7f4;background:#071310}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#12362d,#071310 48%);min-height:100vh}main{max-width:1100px;margin:auto;padding:28px 18px 60px}.hero{padding:28px;border:1px solid #244d42;border-radius:24px;background:#0b211cdd;box-shadow:0 20px 60px #0006}h1{font-size:clamp(32px,6vw,58px);margin:0 0 8px}.sub{color:#a9c9c0;margin:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:18px}.card{background:#0c201b;border:1px solid #244d42;border-radius:18px;padding:18px;min-height:150px}.label{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#7fa99f}.value{font-size:32px;font-weight:750;margin:10px 0}.small{color:#a9c9c0;font-size:14px;line-height:1.45}.good{color:#8de0b8}.warn{color:#ffd27d}.bad{color:#ff9e9e}button{margin-top:20px;border:0;border-radius:12px;padding:12px 16px;font-weight:700;cursor:pointer;background:#dff8ef;color:#082019}.section{margin-top:28px}.section h2{font-size:24px}ul{padding-left:20px}.source{margin-top:24px;color:#77968e;font-size:12px}a{color:#aee7d2}.loading{opacity:.65}
</style></head><body><main><section class="hero"><div class="label">OURPLANETANALYZING · 2.0 MVP</div><h1>Dziennik Planety</h1><p class="sub">Dane środowiskowe, geofizyczne i lokalne w jednym miejscu. Pomiar ≠ prognoza ≠ wniosek.</p><button onclick="load()">Odśwież dane</button></section><section class="grid" id="cards"><div class="card loading">Ładowanie danych…</div></section><section class="section card"><h2>Legnica — grzyby</h2><div id="mush" class="small">Ładowanie…</div></section><section class="section card"><h2>Ostatnie trzęsienia ziemi</h2><ul id="quakes" class="small"></ul></section><div class="source">Źródła danych: NOAA GML, USGS, Open-Meteo. Wskaźnik grzybowy jest heurystyką i nie zastępuje obserwacji terenowych.</div></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){document.getElementById('cards').innerHTML='<div class="card loading">Odświeżanie…</div>';try{const d=await (await fetch('/api/summary')).json();render(d)}catch(e){document.getElementById('cards').innerHTML='<div class="card bad">Błąd pobierania danych.</div>'}}
function render(d){const c=d.co2?.latest, l=d.legnica, q=d.earthquakes;document.getElementById('cards').innerHTML=`<div class="card"><div class="label">CO₂</div><div class="value">${c?esc(c.co2)+' ppm':'—'}</div><div class="small">NOAA GML · Mauna Loa · ostatni dostępny odczyt</div></div><div class="card"><div class="label">Trzęsienia · 24 h</div><div class="value">${esc(q?.count??'—')}</div><div class="small">USGS · wszystkie magnitudy w strumieniu dobowym</div></div><div class="card"><div class="label">Legnica · teraz</div><div class="value">${esc(l?.current?.temperature_2m??'—')} °C</div><div class="small">Wilgotność ${esc(l?.current?.relative_humidity_2m??'—')}% · opad ${esc(l?.current?.precipitation??'—')} mm</div></div>`;document.getElementById('mush').innerHTML=`<b class="${l?.mushroom_score>=70?'good':l?.mushroom_score>=45?'warn':'bad'}">${esc(l?.mushroom_score??'—')}/100</b> · ostatnie 7 dni: ${esc(l?.rain_7d_mm??'—')} mm opadu, średnio ${esc(l?.avg_temp_7d_c??'—')} °C i ${esc(l?.avg_humidity_7d_pct??'—')}% wilgotności.<br><br>${esc(l?.mushroom_note??'')}`;document.getElementById('quakes').innerHTML=(q?.events||[]).slice(0,10).map(x=>`<li>M${esc(x.magnitude)} · ${esc(x.place)}</li>`).join('')||'<li>Brak danych</li>'}
load();setInterval(load,300000);
</script></body></html>'''
