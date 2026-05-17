from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="OurPlanetAnalyzing API",
    version="1.0.0",
    description="API do analizy klimatu, srodowiska i danych geofizycznych.",
)


class AnalyzeRequest(BaseModel):
    question: str = Field(
        ...,
        examples=["Sprawdz emisje CO2 w Europie"],
        description="Pytanie lub temat analizy dotyczacy stanu planety.",
    )
    output_format: Literal["json", "pdf"] = Field(
        "json",
        description="Preferowany format odpowiedzi.",
    )


class AnalyzeResponse(BaseModel):
    response: str
    sources: list[str]
    generated_at: datetime


class ReportResponse(BaseModel):
    report_id: str
    format: Literal["pdf", "json"]
    status: Literal["generated"]
    summary: str


class StatusResponse(BaseModel):
    status: Literal["ok"]
    model: str
    generated_at: datetime


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        response=(
            "Przykladowa analiza: dane klimatyczne i srodowiskowe wymagaja "
            f"dalszej walidacji dla pytania: {request.question}"
        ),
        sources=["NASA", "ESA", "WMO", "IPCC"],
        generated_at=datetime.now(timezone.utc),
    )


@app.post("/generate-report", response_model=ReportResponse)
def generate_report(request: AnalyzeRequest) -> ReportResponse:
    return ReportResponse(
        report_id="ourplanet-demo-report",
        format=request.output_format,
        status="generated",
        summary="Wygenerowano przykladowy raport na podstawie przekazanego pytania.",
    )


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(
        status="ok",
        model="OurPlanetAnalyzing",
        generated_at=datetime.now(timezone.utc),
    )
