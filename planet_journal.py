"""Deterministic, source-aware Planet Journal generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _publication_metadata(retrieved_at: Any) -> dict[str, Any]:
    """Describe weekly publication cadence without mislabeling the measurement period."""
    try:
        generated = datetime.fromisoformat(str(retrieved_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        generated = datetime.now(timezone.utc)
    iso_year, week, _ = generated.isocalendar()
    return {
        "type": "weekly",
        "week": f"{iso_year}-W{week:02d}",
        "generated_at": generated.isoformat(),
    }


def build_planet_journal(
    analysis: dict[str, Any],
    *,
    title: str = "Dziennik Planety",
) -> dict[str, Any]:
    """Build a human-readable journal entry without inventing measurements."""
    points = analysis.get("points")
    if not isinstance(points, dict):
        points = {}

    valid_points = [
        (name, point)
        for name, point in points.items()
        if isinstance(point, dict) and point.get("mean") is not None
    ]

    trends = [
        point.get("trend")
        for _, point in valid_points
        if isinstance(point.get("trend"), dict)
    ]
    rising = [item for item in trends if item.get("direction") == "wzrost"]
    falling = [item for item in trends if item.get("direction") == "spadek"]
    anomalies = []
    for name, point in valid_points:
        point_anomalies = point.get("anomalies", [])
        if isinstance(point_anomalies, list):
            anomalies.extend(
                {"point": name, **item}
                for item in point_anomalies
                if isinstance(item, dict)
            )

    qualities = [
        point.get("data_quality")
        for _, point in valid_points
        if isinstance(point.get("data_quality"), dict)
    ]
    complete = sum(1 for quality in qualities if quality.get("quality") == "complete")
    partial = sum(1 for quality in qualities if quality.get("quality") == "partial")

    period = analysis.get("period", {})
    provider = analysis.get("provider", "nieznany")
    method = analysis.get("method", "brak opisu metody")
    generated_at = analysis.get("retrieved_at")
    publication = _publication_metadata(generated_at)

    observations = [
        f"Przeanalizowano {len(valid_points)} punktów reprezentatywnych."
    ]
    if rising:
        observations.append(f"Wzrost średniej rocznej od początku do końca okresu odnotowano w {len(rising)} punktach.")
    if falling:
        observations.append(f"Spadek średniej rocznej od początku do końca okresu odnotowano w {len(falling)} punktach.")
    if anomalies:
        observations.append(f"Wykryto {len(anomalies)} odchyleń przekraczających ustalony próg.")
    if not rising and not falling and valid_points:
        observations.append("W dostępnych punktach nie odnotowano jednoznacznego kierunku zmiany według zastosowanej reguły.")

    limitations = [
        "Wynik nie jest średnią powierzchniową regionu.",
        "Jeden punkt reprezentatywny nie opisuje całej powierzchni województwa ani kraju.",
        "Trend opisuje różnicę między pierwszą i ostatnią roczną średnią; nie jest prognozą.",
    ]
    if partial:
        limitations.append(f"{partial} punktów ma niepełne dane miesięczne.")

    return {
        "title": title,
        "generated_at": generated_at,
        "publication": publication,
        "period": period,
        "provider": provider,
        "method": method,
        "summary": " ".join(observations),
        "observations": observations,
        "coverage": {
            "valid_points": len(valid_points),
            "total_points": len(points),
            "complete_points": complete,
            "partial_points": partial,
        },
        "source_urls": sorted({
            point.get("source_url")
            for _, point in valid_points
            if isinstance(point.get("source_url"), str) and point.get("source_url")
        }),
        "data_quality": qualities,
        "anomalies": {
            "count": len(anomalies),
            "items": anomalies,
        },
        "limitations": limitations,
    }


def render_weekly_journal_markdown(journal: dict[str, Any]) -> str:
    """Render a compact weekly journal entry from already verified data."""
    title = journal.get("title", "Dziennik Planety")
    period = journal.get("period", {})
    publication = journal.get("publication", {})
    coverage = journal.get("coverage", {})
    anomalies = journal.get("anomalies", {})
    lines = [
        f"# {title}",
        "",
        f"**Publikacja:** {publication.get('type', 'brak')} · {publication.get('week', 'brak')}",
        f"**Okres danych:** {period.get('start', 'brak')}–{period.get('end', 'brak')}",
        f"**Źródło:** {journal.get('provider', 'nieznane')}",
        "",
        "## Co pokazują dane",
    ]
    lines.extend(f"- {item}" for item in journal.get("observations", []))
    lines.extend([
        "",
        "## Jakość danych",
        f"- Poprawne punkty: {coverage.get('valid_points', 0)}/{coverage.get('total_points', 0)}",
        f"- Kompletne serie: {coverage.get('complete_points', 0)}",
        f"- Częściowe serie: {coverage.get('partial_points', 0)}",
        f"- Wykryte anomalie: {anomalies.get('count', 0)}",
        "",
        "## Metoda i ograniczenia",
        f"- {journal.get('method', 'brak opisu metody')}",
    ])
    lines.extend(f"- {item}" for item in journal.get("limitations", []))
    lines.extend([
        "",
        "## Źródła",
    ])
    lines.extend(f"- {url}" for url in journal.get("source_urls", []))
    return "\n".join(lines)
