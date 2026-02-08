from app.services.log_parser import parse_log_line


def test_parse_log_line_extracts_fields() -> None:
    line = (
        "2024-03-01T01:05:00Z ERROR api-gateway latency_ms=450 request_id=req-123 message=timeout hitting db"
    )
    result = parse_log_line(line)
    assert result is not None
    assert result.service == "api-gateway"
    assert result.level == "ERROR"
    assert result.latency_ms == 450
    assert result.request_id == "req-123"
    assert "db" in (result.context or {}).get("message", "") or result.message
