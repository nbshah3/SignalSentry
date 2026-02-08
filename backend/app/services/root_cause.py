from __future__ import annotations

import json
from dataclasses import dataclass, field
from statistics import StatisticsError, correlation
from typing import Dict, Iterable, List, Sequence, Tuple

from sqlmodel import Session

from app.crud import logs as log_crud, metrics as metric_crud
from app.models import Incident
from app.schemas.root_cause import Evidence, Hypothesis, RootCauseResponse
from app.services.incident_detector import DEFAULT_METRICS


@dataclass
class EvidenceItem:
    source: str
    detail: str


@dataclass
class HypothesisResult:
    title: str
    confidence: int
    evidence: List[EvidenceItem] = field(default_factory=list)


class RootCauseAnalyzer:
    KEYWORD_RULES: Dict[str, str] = {
        "timeout": "Likely DB saturation or downstream timeout",
        "db saturation": "Likely DB saturation or slow queries",
        "5xx": "Upstream dependency failure",
        "connection reset": "Downstream dependency failure",
        "dns": "DNS or networking instability",
        "memory leak": "Memory leak / OOM risk",
        "oom": "Memory leak / OOM risk",
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def analyze(self, incident: Incident) -> RootCauseResponse:
        metric_context = self._collect_metric_context(incident)
        logs = log_crud.get_logs_for_window(
            self.session,
            service=incident.service,
            window_start=incident.window_start,
            window_end=incident.window_end,
        )

        hypotheses: List[HypothesisResult] = []
        hypotheses.extend(self._metric_hypotheses(incident, metric_context))
        hypotheses.extend(self._keyword_hypotheses(incident, logs))

        seen_titles = set()
        ordered: List[HypothesisResult] = []
        for hypothesis in sorted(hypotheses, key=lambda h: h.confidence, reverse=True):
            if hypothesis.title in seen_titles:
                continue
            ordered.append(hypothesis)
            seen_titles.add(hypothesis.title)
            if len(ordered) == 3:
                break

        return RootCauseResponse(
            incident_id=incident.id,
            service=incident.service,
            metric=incident.metric,
            hypotheses=[
                Hypothesis(
                    title=hyp.title,
                    confidence=hyp.confidence,
                    evidence=[Evidence(type=item.source, detail=item.detail) for item in hyp.evidence],
                )
                for hyp in ordered
            ],
        )

    def _collect_metric_context(self, incident: Incident) -> Dict[str, List[Tuple[str, float]]]:
        metrics_for_service = metric_crud.get_metrics_for_service(self.session, incident.service)
        to_pull = set(metrics_for_service) | set(DEFAULT_METRICS)
        to_pull.add(incident.metric)
        context: Dict[str, List[Tuple[str, float]]] = {}

        for metric in to_pull:
            series = metric_crud.get_metrics_window(
                session=self.session,
                service=incident.service,
                metric=metric,
                window_start=incident.window_start,
                window_end=incident.window_end,
            )
            if not series:
                continue
            context[metric] = [
                (
                    point.timestamp.replace(second=0, microsecond=0).isoformat(),
                    point.value,
                )
                for point in series
            ]
        return context

    def _metric_hypotheses(
        self,
        incident: Incident,
        context: Dict[str, List[Tuple[str, float]]],
    ) -> List[HypothesisResult]:
        results: List[HypothesisResult] = []
        if incident.metric not in context:
            return results

        primary_series = context[incident.metric]
        for metric, series in context.items():
            if metric == incident.metric:
                continue
            aligned = self._aligned_values(primary_series, series)
            if len(aligned[0]) < 4:
                continue
            corr = self._correlation(aligned[0], aligned[1])
            if corr is None or abs(corr) < 0.65:
                continue
            direction = "positive" if corr > 0 else "negative"
            title = self._metric_title(incident.metric, metric, direction)
            confidence = min(95, int(abs(corr) * 100))
            evidence = EvidenceItem(
                source="metric",
                detail=f"{incident.metric} and {metric} correlation {corr:.2f} across incident window",
            )
            results.append(HypothesisResult(title=title, confidence=confidence, evidence=[evidence]))

        # specialized heuristics
        if incident.metric == "memory_rss_mb":
            slope = self._slope(primary_series)
            if slope > 2:
                evidence = EvidenceItem(
                    source="metric",
                    detail=f"Memory usage increased {slope:.1f} MB/minute during window",
                )
                results.append(
                    HypothesisResult(
                        title="Memory leak / OOM risk",
                        confidence=min(95, 60 + incident.severity // 3),
                        evidence=[evidence],
                    )
                )
        return results

    def _keyword_hypotheses(self, incident: Incident, logs) -> List[HypothesisResult]:
        by_title: Dict[str, HypothesisResult] = {}
        for log in logs:
            tokens = [log.message.lower()]
            if log.context:
                try:
                    payload = json.loads(log.context)
                    tokens.append(json.dumps(payload).lower())
                except json.JSONDecodeError:
                    tokens.append(log.context.lower())
            haystack = " ".join(tokens)
            for keyword, title in self.KEYWORD_RULES.items():
                if keyword in haystack:
                    evidence = EvidenceItem(
                        source="log",
                        detail=f"{log.timestamp.isoformat()} - {log.message}",
                    )
                    confidence = min(90, 55 + incident.severity // 4)
                    current = by_title.get(title)
                    if current:
                        current.evidence.append(evidence)
                        current.confidence = max(current.confidence, confidence)
                    else:
                        by_title[title] = HypothesisResult(
                            title=title, confidence=confidence, evidence=[evidence]
                        )
        return list(by_title.values())

    @staticmethod
    def _aligned_values(
        primary: Sequence[Tuple[str, float]],
        secondary: Sequence[Tuple[str, float]],
    ) -> Tuple[List[float], List[float]]:
        primary_map = {ts: value for ts, value in primary}
        secondary_map = {ts: value for ts, value in secondary}
        keys = sorted(set(primary_map.keys()) & set(secondary_map.keys()))
        return [primary_map[k] for k in keys], [secondary_map[k] for k in keys]

    @staticmethod
    def _correlation(a: Iterable[float], b: Iterable[float]) -> float | None:
        series_a = list(a)
        series_b = list(b)
        if len(series_a) < 2 or len(series_b) < 2:
            return None
        try:
            return correlation(series_a, series_b)
        except StatisticsError:
            return None

    @staticmethod
    def _metric_title(primary: str, secondary: str, direction: str) -> str:
        if primary == "latency_p95_ms" and secondary == "error_rate":
            return "Likely DB saturation impacting latency"
        if primary == "latency_p95_ms" and secondary == "cpu_pct":
            return "CPU contention correlates with latency"
        if primary == "error_rate" and secondary == "latency_p95_ms":
            return "Increased latency correlates with error rate"
        if primary == "memory_rss_mb":
            return "Memory pressure correlates with other metrics"
        return f"{secondary} {direction} correlation"

    @staticmethod
    def _slope(series: Sequence[Tuple[str, float]]) -> float:
        if len(series) < 2:
            return 0.0
        start = series[0][1]
        end = series[-1][1]
        duration = max(len(series) - 1, 1)
        return (end - start) / duration
