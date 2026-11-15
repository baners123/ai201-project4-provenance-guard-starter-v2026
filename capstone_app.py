#!/usr/bin/env python3
"""Provenance Guard with the Unit 9 observability extension."""

from __future__ import annotations

import time

from flask import g, jsonify, request

import app as base_app
import config
import observability
import stylometry

app = base_app.app


def _input_summary() -> dict:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        creator_id = payload.get("creator_id")
        text = payload.get("text")
        record = {"creator_id": creator_id if isinstance(creator_id, str) else None}

        if isinstance(text, str):
            cleaned = text.strip()
            record.update({
                "input_preview": cleaned[:160],
                "input_chars": len(cleaned),
                "input_words": len(stylometry.words(cleaned)),
            })
        elif "text" in payload:
            record.update({
                "input_preview": repr(text)[:160],
                "input_chars": None,
                "input_words": None,
            })

        if request.path == "/appeal":
            record["content_id"] = payload.get("content_id")
            reasoning = payload.get("reasoning")
            if isinstance(reasoning, str):
                record["reasoning_preview"] = reasoning.strip()[:160]
        return record

    raw = request.get_data(as_text=True)
    return {
        "creator_id": None,
        "input_preview": raw[:160] if raw else "",
        "input_chars": len(raw) if raw else 0,
        "input_words": None,
    }


@app.before_request
def capstone_start_timer():
    g.capstone_started = time.perf_counter()


@app.after_request
def capstone_record_run(response):
    started = getattr(g, "capstone_started", None)
    duration_ms = round((time.perf_counter() - started) * 1000, 2) if started is not None else None

    output = response.get_json(silent=True)
    if not isinstance(output, dict):
        output = {}

    record = {
        "timestamp": observability.now_iso(),
        "method": request.method,
        "route": request.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        **_input_summary(),
        "output_guess": output.get("guess"),
        "output_confidence": output.get("confidence"),
        "output_status": output.get("status"),
        "output_error": output.get("error"),
    }
    observability.append_run(record)
    return response


@app.get("/metrics")
def capstone_metrics():
    return jsonify(observability.summarize())


def main():
    print(f"Provenance Guard Capstone on http://{config.HOST}:{config.PORT}")
    print(f"detector model: {config.DETECTOR_MODEL}")
    print(f"structured run log: {observability.RUN_LOG}")
    print("observability endpoint: /metrics")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
