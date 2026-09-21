"""Pure functions for small, explainable environmental trend analysis."""

from __future__ import annotations

from statistics import mean
from typing import Any


def _values(records: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for record in records:
        value = record.get(field)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def summarize(records: list[dict[str, Any]], field: str = "temperature_avg") -> dict[str, Any]:
    values = _values(records, field)
    if not values:
        return {"count": 0, "field": field, "mean": None, "min": None, "max": None, "trend": "brak danych"}

    trend = "stabilny"
    if len(values) >= 2:
        delta = values[-1] - values[0]
        if delta > 0.5:
            trend = "wzrost"
        elif delta < -0.5:
            trend = "spadek"

    return {
        "count": len(values),
        "field": field,
        "mean": round(mean(values), 3),
        "min": min(values),
        "max": max(values),
        "first": values[0],
        "last": values[-1],
        "delta": round(values[-1] - values[0], 3) if len(values) >= 2 else 0.0,
        "trend": trend,
    }


def detect_anomalies(records: list[dict[str, Any]], field: str = "temperature_avg", threshold: float = 2.0) -> list[dict[str, Any]]:
    values = _values(records, field)
    if len(values) < 2:
        return []
    baseline = mean(values)
    return [
        {"date": record.get("date"), "value": value, "deviation": round(value - baseline, 3)}
        for record in records
        for value in [record.get(field)]
        if isinstance(value, (int, float)) and abs(float(value) - baseline) >= threshold
    ]


def compare_periods(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    field: str = "temperature_avg",
) -> dict[str, Any]:
    """Compare two periods without turning the difference into a forecast."""
    current_values = _values(current, field)
    previous_values = _values(previous, field)
    if not current_values or not previous_values:
        return {
            "field": field,
            "current_mean": round(mean(current_values), 3) if current_values else None,
            "previous_mean": round(mean(previous_values), 3) if previous_values else None,
            "change": None,
            "direction": "brak danych",
        }
    current_mean = mean(current_values)
    previous_mean = mean(previous_values)
    change = current_mean - previous_mean
    direction = "wzrost" if change > 0.5 else "spadek" if change < -0.5 else "bez istotnej zmiany"
    return {
        "field": field,
        "current_mean": round(current_mean, 3),
        "previous_mean": round(previous_mean, 3),
        "change": round(change, 3),
        "direction": direction,
    }


def build_signal_summary(
    records: list[dict[str, Any]],
    field: str = "temperature_avg",
    anomaly_threshold: float = 2.0,
) -> dict[str, Any]:
    """Return explainable trend/anomaly signals for journal/report layers."""
    summary = summarize(records, field)
    anomalies = detect_anomalies(records, field, anomaly_threshold)
    return {
        "summary": summary,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "interpretation": (
            "wykryto odchylenia od średniej"
            if anomalies
            else "brak odchyleń przekraczających ustalony próg"
            if summary["count"]
            else "brak danych"
        ),
    }
