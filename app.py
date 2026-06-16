import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(
    title="OurPlanetAnalyzing API",
    version="1.1.0",
    description="Aplikacja do demonstracyjnej analizy klimatu,srodowiska i danych geofizycznych.",
)


class AnalyzeRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        examples=["Sprawdz emisje CO2 w Europie"],
        description="Pytanie lub temat analizy dotyczacy stanu planety.",
    )
    output_format: Literal["json", "markdown"] = Field(
        "json",
        description="Preferowany format odpowiedzi.",
    )


class AnalyzeResponse(BaseModel):
    response: str
    risk_level: Literal["niski", "umiarkowany", "wysoki"]
    recommendations: list[str]
    sources: list[str]
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
    "temperatura": "wzrost temperatur",
    "susza": "ryzyko suszy",
}

SOURCES = ["NASA", "ESA", "WMO", "IPCC"]


def build_analysis(question: str) -> tuple[str, str, list[str]]:
    normalized = question.lower()
    detected = [
        label for keyword, label in KEYWORD_SIGNALS.items() if keyword in normalized
    ]

    if len(detected) >= 2:
        risk_level: Literal["niski", "umiarkowany", "wysoki"] = "wysoki"
    elif detected:
        risk_level = "umiarkowany"
    else:
        risk_level = "niski"

    topics = ", ".join(detected) if detected else "ogolny stan srodowiska"
    response = (
        f"Analiza tematu: {question}. Wykryte obszary: {topics}. "
        "To demonstracyjna odpowiedz aplikacji; do decyzji naukowych nalezy "
        "podlaczyc zweryfikowane dane zrodlowe i model analityczny."
    )

    recommendations = [
        "Porownaj dane z co najmniej dwoch niezaleznych zrodel.",
        "Sprawdz trend w czasie, a nie tylko pojedynczy odczyt.",
        "Oznacz niepewnosc pomiaru i date ostatniej aktualizacji danych.",
    ]

    return response, risk_level, recommendations


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OurPlanetAnalyzing</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f4f7f6;
      color: #17211f;
    }
    main {
      max-width: 920px;
      margin: 0 auto;
      padding: 40px 18px;
    }
    h1 {
      margin: 0 0 10px;
      font-size: 34px;
    }
    p {
      line-height: 1.55;
    }
    form {
      margin-top: 24px;
      display: grid;
      gap: 12px;
    }
    textarea, select, button {
      font: inherit;
      border: 1px solid #bdcbc7;
      border-radius: 8px;
    }
    textarea {
      min-height: 130px;
      padding: 12px;
      resize: vertical;
    }
    select, button {
      padding: 10px 12px;
    }
    button {
      cursor: pointer;
      border-color: #205c50;
      background: #205c50;
      color: white;
      font-weight: 700;
    }
    pre {
      overflow: auto;
      white-space: pre-wrap;
      background: #10201d;
      color: #e8fff8;
      padding: 16px;
      border-radius: 8px;
      min-height: 120px;
    }
  </style>
</head>
<body>
  <main>
    <h1>OurPlanetAnalyzing</h1>
    <p>Wpisz pytanie dotyczace klimatu, srodowiska albo geofizyki i uruchom demonstracyjna analize.</p>
    <form id="analysis-form">
      <textarea id="question" required minlength="3">Sprawdz emisje CO2 w Europie i wplyw na klimat</textarea>
      <select id="output_format">
        <option value="json">JSON</option>
        <option value="markdown">Markdown</option>
      </select>
      <button type="submit">Analizuj</button>
    </form>
    <h2>Wynik</h2>
    <pre id="result">Czekam na pytanie...</pre>
  </main>
  <script>
    const form = document.getElementById("analysis-form");
    const result = document.getElementById("result");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      result.textContent = "Analizuje...";
      const payload = {
        question: document.getElementById("question").value,
        output_format: document.getElementById("output_format").value
      };
      const response = await fetch("/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      result.textContent = JSON.stringify(data, null, 2);
    });
  </script>
</body>
</html>
"""


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    response, risk_level, recommendations = build_analysis(request.question)
    return AnalyzeResponse(
        response=response,
        risk_level=risk_level,
        recommendations=recommendations,
        sources=SOURCES,
        generated_at=datetime.now(timezone.utc),
    )


@app.post("/generate-report", response_model=ReportResponse)
def generate_report(request: AnalyzeRequest) -> ReportResponse:
    response, risk_level, recommendations = build_analysis(request.question)
    generated_at = datetime.now(timezone.utc)

    if request.output_format == "json":
        content = json.dumps(
            {
                "question": request.question,
                "risk_level": risk_level,
                "analysis": response,
                "recommendations": recommendations,
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        content = (
            "# Raport OurPlanetAnalyzing\n\n"
            f"## Pytanie\n{request.question}\n\n"
            f"## Poziom ryzyka\n{risk_level}\n\n"
            f"## Analiza\n{response}\n\n"
            "## Rekomendacje\n"
            + "\n".join(f"- {item}" for item in recommendations)
        )

    return ReportResponse(
        report_id=f"ourplanet-{generated_at.strftime('%Y%m%d%H%M%S')}",
        format=request.output_format,
        status="generated",
        summary=f"Raport wygenerowany dla pytania: {request.question}",
        content=content,
        generated_at=generated_at,
    )


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(
        status="ok",
        app_name="OurPlanetAnalyzing",
        version=app.version,
        generated_at=datetime.now(timezone.utc),
    )
