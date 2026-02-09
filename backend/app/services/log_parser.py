from __future__ import annotations

import re
import shlex
from datetime import datetime
from typing import List, Optional

from app.schemas import LogCreate

_TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%d/%b/%Y:%H:%M:%S",
]

_KV_PATTERN = re.compile(r"(?P<key>[A-Za-z_][\w\-]*)=(?P<value>[^\s]+)")


def _parse_timestamp(value: str) -> Optional[datetime]:
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        pass

    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def parse_log_line(line: str) -> Optional[LogCreate]:
    raw = line.strip()
    if not raw:
        return None

    tokens = shlex.split(raw)
    if not tokens:
        return None

    idx = 0
    timestamp = _parse_timestamp(tokens[0])
    if timestamp:
        idx += 1
    else:
        timestamp = datetime.utcnow()

    level = "INFO"
    if (
        idx < len(tokens)
        and tokens[idx].isalpha()
        and tokens[idx].upper() == tokens[idx]
    ):
        level = tokens[idx].upper()
        idx += 1

    service = None
    if idx < len(tokens) and "=" not in tokens[idx]:
        service = tokens[idx]
        idx += 1

    kv_store = {}
    message_tokens: List[str] = []

    for token in tokens[idx:]:
        if "=" in token:
            key, value = token.split("=", 1)
            kv_store[key.lower()] = value.strip('"')
        else:
            message_tokens.append(token)

    # Allow embedded key/value pairs that weren't caught due to quoting
    for match in _KV_PATTERN.finditer(raw):
        kv_store.setdefault(match.group("key").lower(), match.group("value"))

    timestamp = _parse_timestamp(kv_store.get("timestamp", str(timestamp))) or timestamp
    level = kv_store.get("level", level).upper()
    service = kv_store.get("service", service or "unknown")

    message = kv_store.get("message") or " ".join(message_tokens).strip()
    if not message:
        message = raw

    request_id = kv_store.get("request_id") or kv_store.get("requestid")
    latency_raw = kv_store.get("latency_ms") or kv_store.get("latency")
    latency_ms = None
    if latency_raw:
        latency_ms = _parse_latency(latency_raw)

    context_keys = {
        "timestamp",
        "level",
        "service",
        "message",
        "request_id",
        "requestid",
        "latency_ms",
        "latency",
    }
    context = {k: v for k, v in kv_store.items() if k not in context_keys}
    if not context:
        context = None

    return LogCreate(
        timestamp=timestamp,
        service=service,
        level=level,
        request_id=request_id,
        message=message,
        latency_ms=latency_ms,
        context=context,
    )


def _parse_latency(value: str) -> Optional[float]:
    cleaned = value.lower().replace("ms", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_log_blob(blob: str) -> List[LogCreate]:
    entries: List[LogCreate] = []
    for line in blob.splitlines():
        parsed = parse_log_line(line)
        if parsed:
            entries.append(parsed)
    return entries
