"""Deterministic, source-aware Planet Journal generation."""

from __future__ import annotations

from typing import Any


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
        "generated_at": analysis.get("retrieved_at"),
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
