import pytest

from planet_agent import create_planet_agent, get_poland_temperature_analysis_data, run_planet_agent


def test_planet_agent_has_expected_tool():
    agent = create_planet_agent()
    assert agent.name == "Planet Agent"
    assert len(agent.tools) == 1


@pytest.mark.asyncio
async def test_planet_agent_data_tool_exposes_provenance(monkeypatch):
    async def fake_build(points, region_name):
        assert region_name == "Polska"
        assert len(points) == 16
        return {
            "live_data": True,
            "provider": "NASA POWER",
            "region": "Polska",
            "period": {"start": "2019-01", "end": "2025-12"},
            "method": "one representative NASA POWER point per region; not an area-weighted polygon average",
            "points": {},
            "retrieved_at": "2026-09-20T00:00:00+00:00",
        }

    monkeypatch.setattr("planet_agent.build_regional_temperature", fake_build)

    data = await get_poland_temperature_analysis_data()

    assert data["live_data"] is True
    assert data["provider"] == "NASA POWER"
    assert data["period"] == {"start": "2019-01", "end": "2025-12"}
    assert "not an area-weighted polygon average" in data["method"]


@pytest.mark.asyncio
async def test_planet_agent_data_tool_does_not_call_network_in_unit_test(monkeypatch):
    async def fake_build(points, region_name):
        return {
            "live_data": True,
            "provider": "NASA POWER",
            "region": region_name,
            "period": {"start": "2019-01", "end": "2025-12"},
            "method": "one representative NASA POWER point per region; not an area-weighted polygon average",
            "points": {},
            "retrieved_at": "2026-09-20T00:00:00+00:00",
        }

    monkeypatch.setattr("planet_agent.build_regional_temperature", fake_build)

    data = await get_poland_temperature_analysis_data()

    assert data["region"] == "Polska"
    assert data["points"] == {}


@pytest.mark.asyncio
async def test_planet_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        await run_planet_agent("Jaki jest trend temperatury w Polsce?")
