from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import fmean, pstdev
from typing import Iterable, Sequence

POSITIVE_ONLY_METRICS = {"latency_p95_ms", "error_rate", "memory_rss_mb", "cpu_pct"}


@dataclass
class AnomalyAssessment:
    severity: int
    baseline: float
    observed: float
    window_start: datetime
    window_end: datetime
    detector: str
    summary: str


def _safe_mean(values: Sequence[float]) -> float:
    return fmean(values) if values else 0.0


def _z_score(series: Sequence[float], observed: float) -> float:
    if len(series) < 2:
        return 0.0
    sigma = pstdev(series)
    if sigma == 0:
        return 0.0
    return (observed - _safe_mean(series)) / sigma


def _ewma(series: Sequence[float], alpha: float = 0.3) -> float:
    if not series:
        return 0.0
    estimate = series[0]
    for value in series[1:]:
        estimate = alpha * value + (1 - alpha) * estimate
    return estimate


def detect_anomaly(
    values: Sequence[float],
    timestamps: Sequence[datetime],
    metric: str,
    window_size: int = 5,
    min_points: int = 20,
) -> AnomalyAssessment | None:
    if len(values) < max(window_size * 2, min_points):
        return None

    baseline_window = values[:-window_size]
    recent_window = values[-window_size:]
    baseline = _safe_mean(baseline_window[-window_size * 3 :])
    observed = _safe_mean(recent_window)
    if baseline == 0 and metric in POSITIVE_ONLY_METRICS:
        baseline = 1e-6

    if metric in POSITIVE_ONLY_METRICS and observed <= baseline * 1.05:
        return None

    z_val = abs(_z_score(baseline_window, observed))
    ewma_baseline = _ewma(baseline_window)
    ewma_delta = abs(observed - ewma_baseline)
    pct_change = abs((observed - baseline) / (abs(baseline) + 1e-6))

    severity_score = pct_change * 45 + z_val * 20 + (ewma_delta / (abs(baseline) + 1e-6)) * 25

    severity = min(100, int(round(severity_score)))
    if severity < 55:
        return None

    window_start = timestamps[-window_size]
    window_end = timestamps[-1]

    summary = (
        f"{metric} deviated by {pct_change:.1%} (baseline {baseline:.2f}, observed {observed:.2f})"
    )

    return AnomalyAssessment(
        severity=severity,
        baseline=baseline,
        observed=observed,
        window_start=window_start,
        window_end=window_end,
        detector="zscore_ewma",
        summary=summary,
    )


def detect_for_series(
    series: Iterable[tuple[datetime, float]],
    metric: str,
    window_size: int = 5,
) -> AnomalyAssessment | None:
    timestamps, values = [], []
    for ts, value in series:
        timestamps.append(ts)
        values.append(value)
    return detect_anomaly(values, timestamps, metric=metric, window_size=window_size)
