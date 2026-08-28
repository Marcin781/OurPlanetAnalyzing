from __future__ import annotations


def summarize_series(values_map: dict) -> dict:
    values = [float(v) for v in values_map.values() if isinstance(v, (int, float))]
    years: dict[int, list[float]] = {}
    for key, value in values_map.items():
        if not isinstance(value, (int, float)):
            continue
        try:
            year = int(str(key)[:4])
        except ValueError:
            continue
        years.setdefault(year, []).append(float(value))

    yearly_mean = {str(year): round(sum(vals) / len(vals), 2) for year, vals in sorted(years.items()) if vals}
    trend = None
    if len(yearly_mean) >= 2:
        first_year, last_year = list(yearly_mean)[0], list(yearly_mean)[-1]
        change = yearly_mean[last_year] - yearly_mean[first_year]
        trend = {
            "from_year": int(first_year),
            "to_year": int(last_year),
            "change_degC": round(change, 2),
            "direction": "wzrost" if change > 0 else "spadek" if change < 0 else "bez zmiany",
        }

    return {
        "observations": len(values),
        "min": round(min(values), 2) if values else None,
        "max": round(max(values), 2) if values else None,
        "mean": round(sum(values) / len(values), 2) if values else None,
        "yearly_mean": yearly_mean,
        "trend": trend,
    }
