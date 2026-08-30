from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    metric TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION,
    unit TEXT,
    anomaly DOUBLE PRECISION,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source, metric, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_observations_metric_time ON observations(metric, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_observations_source_time ON observations(source, observed_at DESC);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id BIGSERIAL PRIMARY KEY,
    week_start DATE NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    report JSONB NOT NULL
);
"""


@contextmanager
def connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def init_db() -> None:
    with connection() as conn:
        conn.execute(SCHEMA)
        conn.commit()


def insert_observation(source: str, metric: str, observed_at, value, unit=None, anomaly=None, metadata=None) -> None:
    with connection() as conn:
        conn.execute(
            """INSERT INTO observations(source, metric, observed_at, value, unit, anomaly, metadata)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (source, metric, observed_at) DO UPDATE SET
                 value=EXCLUDED.value, unit=EXCLUDED.unit, anomaly=EXCLUDED.anomaly,
                 metadata=EXCLUDED.metadata""",
            (source, metric, observed_at, value, unit, anomaly, metadata or {}),
        )
        conn.commit()


def recent_observations(metric: str, limit: int = 120):
    with connection() as conn:
        return conn.execute(
            "SELECT source, metric, observed_at, value, unit, anomaly, metadata FROM observations WHERE metric=%s ORDER BY observed_at DESC LIMIT %s",
            (metric, limit),
        ).fetchall()
