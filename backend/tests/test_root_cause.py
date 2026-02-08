from datetime import datetime
from types import SimpleNamespace

from app.models import Incident
from app.services.root_cause import RootCauseAnalyzer


def test_root_cause_keyword_hints(session) -> None:
    incident = Incident(
        incident_key="api:latency",
        service="api-gateway",
        metric="latency_p95_ms",
        severity=80,
        window_start=datetime.utcnow(),
        window_end=datetime.utcnow(),
        baseline=100.0,
        observed=320.0,
    )
    analyzer = RootCauseAnalyzer(session)
    logs = [
        SimpleNamespace(
            message="timeout waiting on db",
            context='{"keyword": "timeout"}',
            timestamp=SimpleNamespace(isoformat=lambda: "2024-03-01T00:00:00Z"),
        )
    ]
    hypotheses = analyzer._keyword_hypotheses(incident, logs)
    assert any("timeout" in hyp.title.lower() or "db" in hyp.title.lower() for hyp in hypotheses)
