"""Planet Agent integration for OurPlanetAnalyzing."""

from __future__ import annotations

import os
from typing import Any

from agents import Agent, Runner, function_tool

from app import build_regional_temperature
from regions import POLISH_VOIVODESHIPS


@function_tool
async def get_poland_temperature_analysis() -> dict[str, Any]:
    """Fetch and summarize NASA POWER temperature data for 16 Polish voivodeships."""
    return await build_regional_temperature(POLISH_VOIVODESHIPS, "Polska")


PLANET_AGENT_INSTRUCTIONS = """
Jesteś Planet Agentem projektu OurPlanetAnalyzing.

Pomagasz analizować dane o klimacie, środowisku i geofizyce.
Nie przedstawiaj przypuszczeń jako pomiarów.

Zasady:
- używaj narzędzia danych, gdy pytanie wymaga danych liczbowych;
- podawaj źródło, okres i metodę danych;
- pojedynczy punkt reprezentatywny nie jest średnią powierzchniową regionu;
- jeśli dane są niepełne albo narzędzie zgłasza błąd, powiedz o tym wprost;
- nie wyznaczaj poziomu ryzyka bez zweryfikowanego modelu;
- oddzielaj obserwację od interpretacji;
- nie wymyślaj danych, źródeł ani wyników;
- jeśli pytanie wykracza poza dostępne dane, jasno określ ograniczenie.
"""


def create_planet_agent() -> Agent:
    """Create the Planet Agent with its deterministic NASA POWER data tool."""
    return Agent(
        name="Planet Agent",
        instructions=PLANET_AGENT_INSTRUCTIONS,
        model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        tools=[get_poland_temperature_analysis],
    )


async def run_planet_agent(question: str) -> str:
    """Run the Planet Agent and return its final text output."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    result = await Runner.run(create_planet_agent(), question)
    return result.final_output
