import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from data_sources import DataSourceError, fetch_nasa_power_temperature, fetch_nasa_power_temperature_points
from regions import POLISH_VOIVODESHIPS


app = FastAPI(
    title="OurPlanetAnalyzing API",
    version="1.3.0",
    description="Analiza klimatu, srodowiska i danych geofizycznych z weryfikowalnym zrodlem danych.",
)


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=3, examples=["Jak zmieniala sie temperatura w Polsce i wojewodztwach?"], description="Pytanie lub temat analizy dotyczacy stanu planety.")
    output_format: Literal["json", "markdown"] = Field("json")


class AnalyzeResponse(BaseModel):
    response: str
    risk_level: Literal["niski", "umiarkowany", "wysoki"]
    recommendations: list[str]
    sources: list[str]
    data: dict
    generated_at: datetime


class ReportResponse(BaseModel):
    report_id: str
    format: Literal["json", "markdown"]
    status: Literal["generated"]
    summary: str
    content: str
    generated_at: datetime


class StatusResponse(BaseModel):
    status: Literal["ok"]
    app_name: str
    version: str
    generated_at: datetime


KEYWORD_SIGNALS = {
    "co2": "emisje gazow cieplarnianych",
    "klimat": "zmiany klimatyczne",
    "lodowiec": "topnienie lodowcow",
    "ocean": "wzrost poziomu oceanow",
    "wulkan": "aktywnosc wulkaniczna",
    "sejs": "aktywnosc sejsmiczna",
    "temperatura": "temperatura powietrza",
    "susza": "ryzyko suszy",
}


async def build_analysis(question: str) -> tuple[str, str, list[str], dict, list[str]]:
    normalized = question.lower()
    detected = [label for keyword, label in KEYWORD_SIGNALS.items() if keyword in normalized]
    risk_level: Literal["niski", "umiarkowany", "wysoki"] = "wysoki" if len(detected) >= 2 else "umiarkowany" if detected else "niski"
    recommendations = [
        "Porownaj dane z co najmniej dwoch niezaleznych zrodel.",
        "Sprawdz trend w czasie, a nie tylko pojedynczy odczyt.",
        "Oznacz niepewnosc pomiaru i date ostatniej aktualizacji danych.",
    ]
    data: dict = {"live_data": False}
    sources: list[str] = []

    if any(word in normalized for word in ("temperatura", "klimat", "europ", "pogod")):
        try:
            nasa = await fetch_nasa_power_temperature(latitude=50.0, longitude=15.0, start_year=2019, end_year=2025)
            values = [float(v) for v in nasa["data"].values() if isinstance(v, (int, float))]
            if values:
                data = {
                    "live_data": True, "provider": nasa["provider"], "parameter": nasa["parameter"], "unit": nasa["unit"],
                    "location": nasa["location"], "period": nasa["period"], "observations": len(values),
                    "min": round(min(values), 2), "max": round(max(values), 2), "mean": round(sum(values) / len(values), 2),
                    "retrieved_at": nasa["retrieved_at"], "source_url": nasa["source_url"],
                    "method": "single representative point; not a regional spatial average",
                }
                sources.append("NASA POWER")
        except DataSourceError as exc:
            data = {"live_data": False, "error": str(exc)}

    if any(word in normalized for word in ("województw", "wojewodztw", "polska", "polsce")) and "temperatur" in normalized:
        regional = await fetch_nasa_power_temperature_points(POLISH_VOIVODESHIPS, 2019, 2025)
        data = {
            "live_data": True,
            "provider": regional["provider"],
            "region": "Polska",
            "period": regional["period"],
            "method": "one representative NASA POWER point per voivodeship; not an area-weighted polygon average",
            "voivodeships": {},
            "retrieved_at": regional["retrieved_at"],
        }
        for key, result in regional["points"].items():
            if "error" in result:
                data["voivodeships"][key] = result
                continue
            values = [float(v) for v in result["data"].values() if isinstance(v, (int, float))]
            data["voivodeships"][key] = {
                "name": POLISH_VOIVODESHIPS[key]["name"],
                "location": result["location"],
                "observations": len(values),
                "mean": round(sum(values) / len(values), 2) if values else None,
                "min": round(min(values), 2) if values else None,
                "max": round(max(values), 2) if values else None,
                "source_url": result["source_url"],
            }
        sources = ["NASA POWER"]

    if not sources:
        sources = ["NASA POWER"]

    if data.get("live_data") and "voivodeships" in data:
        valid = [v["mean"] for v in data["voivodeships"].values() if v.get("mean") is not None]
        response = f"Analiza temperatury Polski dla 16 wojewodztw. Pobrano rzeczywiste dane z NASA POWER za okres 2019-2025. Zastosowano po jednym punkcie reprezentatywnym na wojewodztwo; wynik nie jest jeszcze srednia powierzchniowa. Liczba poprawnie pobranych wojewodztw: {len(valid)}/16."
    elif data.get("live_data"):
        response = f"Analiza tematu: {question}. Pobrano rzeczywiste dane z {data['provider']} dla punktu referencyjnego {data['location']['latitude']}, {data['location']['longitude']}. Zakres danych: {data['period']['start']}-{data['period']['end']}. Srednia temperatura: {data['mean']} {data['unit']}, minimum: {data['min']} {data['unit']}, maksimum: {data['max']} {data['unit']}."
    else:
        response = f"Analiza tematu: {question}. Wykryte obszary: {', '.join(detected) if detected else 'ogolny stan srodowiska'}. Dla tego typu pytania nie ma jeszcze podlaczonego dedykowanego zrodla danych."

    return response, risk_level, recommendations, data, sources


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return """<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OurPlanetAnalyzing</title><style>body{margin:0;font-family:Arial,sans-serif;background:#f4f7f6;color:#17211f}main{max-width:920px;margin:0 auto;padding:40px 18px}h1{margin:0 0 10px;font-size:34px}p{line-height:1.55}form{margin-top:24px;display:grid;gap:12px}textarea,select,button{font:inherit;border:1px solid #bdcbc7;border-radius:8px}textarea{min-height:130px;padding:12px;resize:vertical}select,button{padding:10px 12px}button{cursor:pointer;border-color:#205c50;background:#205c50;color:white;font-weight:700}pre{overflow:auto;white-space:pre-wrap;background:#10201d;color:#e8fff8;padding:16px;border-radius:8px;min-height:120px}</style></head><body><main><h1>OurPlanetAnalyzing</h1><p>Wpisz pytanie dotyczace klimatu, srodowiska albo geofizyki i uruchom analize.</p><form id="analysis-form"><textarea id="question" required minlength="3">Jak zmieniala sie temperatura w Polsce i wojewodztwach?</textarea><select id="output_format"><option value="json">JSON</option><option value="markdown">Markdown</option></select><button type="submit">Analizuj</button></form><h2>Wynik</h2><pre id="result">Czekam na pytanie...</pre></main><script>const form=document.getElementById("analysis-form"),result=document.getElementById("result");form.addEventListener("submit",async(e)=>{e.preventDefault();result.textContent="Analizuje...";try{const r=await fetch("/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:document.getElementById("question").value,output_format:document.getElementById("output_format").value})});result.textContent=JSON.stringify(await r.json(),null,2)}catch(e){result.textContent=JSON.stringify({error:"Nie udalo sie polaczyc z API."},null,2)}});</script></body></html>"""


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    response, risk_level, recommendations, data, sources = await build_analysis(request.question)
    return AnalyzeResponse(response=response, risk_level=risk_level, recommendations=recommendations, sources=sources, data=data, generated_at=datetime.now(timezone.utc))


@app.post("/generate-report", response_model=ReportResponse)
async def generate_report(request: AnalyzeRequest) -> ReportResponse:
    response, risk_level, recommendations, data, sources = await build_analysis(request.question)
    generated_at = datetime.now(timezone.utc)
    report = {"question": request.question, "risk_level": risk_level, "analysis": response, "recommendations": recommendations, "sources": sources, "data": data}
    content = json.dumps(report, ensure_ascii=False, indent=2) if request.output_format == "json" else "# Raport OurPlanetAnalyzing\n\n" + json.dumps(report, ensure_ascii=False, indent=2)
    return ReportResponse(report_id=f"ourplanet-{generated_at.strftime('%Y%m%d%H%M%S')}", format=request.output_format, status="generated", summary=f"Raport wygenerowany dla pytania: {request.question}", content=content, generated_at=generated_at)


@app.get("/poland/voivodeships/temperature")
async def poland_voivodeships_temperature() -> dict:
    """Return live NASA POWER temperature summaries for all 16 Polish voivodeships."""
    regional = await fetch_nasa_power_temperature_points(POLISH_VOIVODESHIPS, 2019, 2025)
    result: dict = {"provider": regional["provider"], "region": "Polska", "period": regional["period"], "method": "one representative point per voivodeship", "voivodeships": {}}
    for key, item in regional["points"].items():
        if "error" in item:
            result["voivodeships"][key] = item
            continue
        values = [float(v) for v in item["data"].values() if isinstance(v, (int, float))]
        result["voivodeships"][key] = {"name": POLISH_VOIVODESHIPS[key]["name"], "mean": round(sum(values)/len(values),2) if values else None, "min": round(min(values),2) if values else None, "max": round(max(values),2) if values else None, "observations": len(values), "location": item["location"], "source_url": item["source_url"]}
    result["retrieved_at"] = regional["retrieved_at"]
    return result


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(status="ok", app_name="OurPlanetAnalyzing", version=app.version, generated_at=datetime.now(timezone.utc))
