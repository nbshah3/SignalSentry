from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models import Incident
from app.schemas.postmortem import PostmortemResponse
from app.schemas.root_cause import RootCauseResponse

ACTION_HINTS: Dict[str, List[str]] = {
    "latency_p95_ms": [
        "Audit database slow queries and connection pool thresholds.",
        "Enable request-level profiling for hottest endpoints.",
    ],
    "error_rate": [
        "Coordinate with upstream dependencies to confirm stability.",
        "Increase canary coverage to detect regressions sooner.",
    ],
    "memory_rss_mb": [
        "Capture heap profiles and add guards for runaway allocations.",
        "Deploy tighter auto-scaling or restart policies for workers.",
    ],
    "cpu_pct": [
        "Throttle expensive jobs and right-size compute reservations.",
    ],
}


@dataclass
class PostmortemArtifacts:
    incident_id: int
    summary: str
    json_path: Path
    pdf_path: Path

    def to_response(self) -> PostmortemResponse:
        return PostmortemResponse(
            incident_id=self.incident_id,
            summary=self.summary,
            json_path=str(self.json_path),
            pdf_path=str(self.pdf_path),
            downloads={
                "json": f"/api/v1/postmortems/{self.json_path.name}",
                "pdf": f"/api/v1/postmortems/{self.pdf_path.name}",
            },
        )


class PostmortemGenerator:
    def __init__(self, export_dir: str) -> None:
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, incident: Incident, analysis: RootCauseResponse) -> PostmortemArtifacts:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        base_name = f"incident_{incident.id}_{timestamp}"
        json_path = self.export_dir / f"{base_name}.json"
        pdf_path = self.export_dir / f"{base_name}.pdf"

        payload = self._build_payload(incident, analysis)
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._write_pdf(pdf_path, payload)

        return PostmortemArtifacts(
            incident_id=incident.id,
            summary=payload["summary"],
            json_path=json_path,
            pdf_path=pdf_path,
        )

    def _build_payload(self, incident: Incident, analysis: RootCauseResponse) -> Dict[str, object]:
        top_hypothesis = (
            analysis.hypotheses[0].title
            if analysis.hypotheses
            else incident.summary or "Incident detected"
        )
        action_items = ACTION_HINTS.get(incident.metric, ["Complete RCA and document mitigations."])
        timeline = [
            {"label": "Window start", "timestamp": incident.window_start.isoformat()},
            {"label": "Window end", "timestamp": incident.window_end.isoformat()},
            {"label": "Detected", "timestamp": incident.detected_at.isoformat()},
        ]
        payload = {
            "summary": top_hypothesis,
            "incident": {
                "id": incident.id,
                "service": incident.service,
                "metric": incident.metric,
                "severity": incident.severity,
                "baseline": incident.baseline,
                "observed": incident.observed,
                "window_start": incident.window_start.isoformat(),
                "window_end": incident.window_end.isoformat(),
            },
            "analysis": analysis.model_dump(),
            "timeline": timeline,
            "action_items": action_items,
        }
        return payload

    def _write_pdf(self, pdf_path: Path, payload: Dict[str, object]) -> None:
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        width, height = letter
        y = height - 72

        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, y, f"Postmortem: Incident {payload['incident']['id']}")
        y -= 24

        c.setFont("Helvetica", 11)
        details = [
            f"Service: {payload['incident']['service']}",
            f"Metric: {payload['incident']['metric']}",
            f"Severity: {payload['incident']['severity']}",
            f"Window: {payload['incident']['window_start']} - {payload['incident']['window_end']}",
            f"Baseline vs Observed: {payload['incident']['baseline']} -> {payload['incident']['observed']}",
        ]
        for line in details:
            c.drawString(72, y, line)
            y -= 16

        y = self._write_section(
            c, y - 8, "Hypotheses", payload["analysis"].get("hypotheses", []), height
        )
        y = self._write_list_section(c, y, "Action Items", payload["action_items"], height)
        y = self._write_list_section(
            c,
            y,
            "Timeline",
            [f"{item['label']}: {item['timestamp']}" for item in payload["timeline"]],
            height,
        )

        c.showPage()
        c.save()

    def _write_section(
        self,
        c: canvas.Canvas,
        y: float,
        title: str,
        hypotheses: List[Dict[str, object]],
        page_height: float,
    ) -> float:
        if y < 120:
            c.showPage()
            y = page_height - 72
        c.setFont("Helvetica-Bold", 13)
        c.drawString(72, y, title)
        y -= 18
        c.setFont("Helvetica", 11)
        if not hypotheses:
            c.drawString(72, y, "(no data)")
            y -= 14
            return y
        for hyp in hypotheses:
            text = f"- {hyp['title']} ({hyp['confidence']}%)"
            c.drawString(72, y, text)
            y -= 14
            for evidence in hyp.get("evidence", []):
                if y < 72:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = page_height - 72
                detail = f"* {evidence['type']}: {evidence['detail'][:120]}"
                c.drawString(90, y, detail)
                y -= 12
        return y

    def _write_list_section(
        self, c: canvas.Canvas, y: float, title: str, items: List[str], page_height: float
    ) -> float:
        if y < 120:
            c.showPage()
            y = page_height - 72
        c.setFont("Helvetica-Bold", 13)
        c.drawString(72, y, title)
        y -= 18
        c.setFont("Helvetica", 11)
        for item in items:
            if y < 72:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = page_height - 72
            c.drawString(72, y, f"- {item}")
            y -= 14
        return y
