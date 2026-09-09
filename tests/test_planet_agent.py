import pytest

from planet_agent import create_planet_agent, run_planet_agent


def test_planet_agent_has_expected_tool():
    agent = create_planet_agent()
    assert agent.name == "Planet Agent"
    assert len(agent.tools) == 1


@pytest.mark.asyncio
async def test_planet_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        await run_planet_agent("Jaki jest trend temperatury w Polsce?")
