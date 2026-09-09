"""Planet Agent integration for OurPlanetAnalyzing.

The agent uses the OpenAI Agents SDK when OPENAI_API_KEY is configured.
The data tools remain deterministic and local to the application, so the
model can explain verified NASA POWER results without inventing measurements.
"""

from __future__ import annotations

import os
from typing import Any

from agents import Agent, Runner, function_tool

from app import build_regional_temperature
from regions import POLISH_VOIVODESHIPS


@function_tool
def get_poland_temperature_analysis() -> dict[str, Any]:
    """Return the latest configured NASA POWER temperature analysis for Poland."""
    raise RuntimeError(
        "This tool is async and must be called through get_poland_temperature_analysis_async."
    )


@function_tool
async def get_poland_temperature_analysis_async() -> dict[str, Any]:
    """Fetch and summarize NASA POWER temperature data for 16 Polish voivodeships."""
    return await build_regional_temperature(POLISH_VOIVODESHIPS, "Polska")


PLANET_AGENT_INSTRUCTIONS = """
Jesteś Planet Agentem projektu OurPlanetAnalyzing.

Twoim zadaniem jest pomagać w analizie danych o klimacie, środowisku i geofizyce.
Najważniejsza zasada: nie przedstawiaj przypuszczeń jako pomiarów.

Zasady:
- korzystaj z narzędzi danych, gdy pytanie dotyczy danych liczbowych;
- wyraźnie podawaj źródło, okres i metodę danych;
- pamiętaj, że pojedynczy punkt reprezentatywny nie jest średnią powierzchniową regionu;
- jeśli dane są niepełne albo narzędzie zgłasza błąd, powiedz o tym wprost;
- nie wyznaczaj poziomu ryzyka środowiskowego bez zweryfikowanego modelu;
- oddzielaj obserwację danych od interpretacji;
- nie wymyślaj danych, źródeł ani wyników.
"""


def create_planet_agent() -> Agent:
    """Create the Planet Agent with its deterministic data tool."""
    return Agent(
        name="Planet Agent",
        instructions=PLANET_AGENT_INSTRUCTIONS,
        model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        tools=[get_poland_temperature_analysis_async],
    )


async def run_planet_agent(question: str) -> str:
    """Run the Planet Agent and return its final text output."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    result = await Runner.run(create_planet_agent(), question)
    return result.final_output
