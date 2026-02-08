from datetime import datetime, timedelta

from app.models import MetricPoint
from app.services.anomaly import detect_anomaly
from app.services.incident_detector import IncidentDetector


def test_detect_anomaly_identifies_spike() -> None:
    start = datetime.utcnow() - timedelta(minutes=40)
    timestamps = [start + timedelta(minutes=i) for i in range(30)]
    values = [100.0 for _ in range(25)] + [200.0 for _ in range(5)]
    assessment = detect_anomaly(values, timestamps, metric="latency_p95_ms")
    assert assessment is not None
    assert assessment.severity >= 55


def test_incident_detector_creates_incident(session, baseline_metrics) -> None:
    now = datetime.utcnow()
    for idx in range(5):
        session.add(
            MetricPoint(
                service="api-gateway",
                metric="latency_p95_ms",
                timestamp=now - timedelta(minutes=5 - idx),
                value=350.0,
            )
        )
    session.commit()

    detector = IncidentDetector(session)
    incident = detector.evaluate_metric("api-gateway", "latency_p95_ms")
    assert incident is not None
    assert incident.severity >= 55
