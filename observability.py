"""Structured observability for the Provenance Guard capstone."""

from __future__ import annotations

import json
import statistics
import threading
from datetime import datetime, timezone

import config

_lock = threading.Lock()
RUN_LOG = config.ROOT / "logs" / "capstone_runs.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def append_run(entry: dict) -> dict:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with _lock:
        with RUN_LOG.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return entry


def read_runs(limit: int | None = None) -> list[dict]:
    if not RUN_LOG.exists():
        return []
    rows = []
    for raw in RUN_LOG.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows[-limit:] if limit else rows


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
    return round(value, 2)


def summarize() -> dict:
    runs = read_runs()
    submits = [r for r in runs if r.get("route") == "/submit"]
    successful_submits = [r for r in submits if 200 <= int(r.get("status_code", 0)) < 300]
    rejected = [r for r in runs if int(r.get("status_code", 0)) >= 400]

    durations = [
        float(r["duration_ms"])
        for r in successful_submits
        if isinstance(r.get("duration_ms"), (int, float))
    ]

    label_counts = {}
    for row in successful_submits:
        label = row.get("output_guess") or "unknown"
        label_counts[label] = label_counts.get(label, 0) + 1

    error_counts = {}
    for row in rejected:
        reason = row.get("output_error") or f"http_{row.get('status_code')}"
        error_counts[reason] = error_counts.get(reason, 0) + 1

    return {
        "total_requests_logged": len(runs),
        "submit_requests": len(submits),
        "successful_submits": len(successful_submits),
        "rejected_or_failed_requests": len(rejected),
        "average_submit_duration_ms": round(statistics.mean(durations), 2) if durations else None,
        "p95_submit_duration_ms": _percentile(durations, 0.95),
        "label_counts": label_counts,
        "error_counts": error_counts,
        "last_run_timestamp": runs[-1].get("timestamp") if runs else None,
        "run_log": str(RUN_LOG),
    }
