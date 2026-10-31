#!/usr/bin/env python3
"""Provenance Guard web service."""

import uuid

from flask import Flask, jsonify, request

import audit
import config
import detector
import scoring
import stylometry

app = Flask(__name__)


class _LimiterOff:
    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()

if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return get_remote_address()

        creator = payload.get("creator_id")
        if isinstance(creator, str) and creator.strip():
            return creator.strip()

        return get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )


@app.errorhandler(429)
def rate_limited(exc):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}

    audit.log_rejection(
        creator_id=payload.get("creator_id", "unknown"),
        reason="rate_limited",
        limit=str(exc.description),
    )

    return jsonify(
        {
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }
    ), 429


def reject(status_code: int, error: str, message: str, creator_id="unknown", **extra):
    audit.log_rejection(
        creator_id=creator_id or "unknown",
        reason=error,
        **extra,
    )
    return jsonify({"error": error, "message": message}), status_code


@app.post("/ping")
def ping():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "ok": True,
            "you_sent": payload.get("message"),
            "service": "provenance-guard",
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "detector_model": config.DETECTOR_MODEL,
            "detector_loaded": detector._model is not None,
            "rate_limiting": config.RATE_LIMITING_ENABLED,
            "log_entries": len(audit.read_entries()),
        }
    )


@app.post("/submit")
@limiter.limit(
    f"{config.RATE_LIMIT_PER_MINUTE}/minute;"
    f"{config.RATE_LIMIT_PER_DAY}/day"
)
def submit():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return reject(
            400,
            "invalid_json",
            "Send a JSON object with text and creator_id.",
        )

    text = payload.get("text")
    creator_id = payload.get("creator_id")

    if not isinstance(creator_id, str) or not creator_id.strip():
        return reject(
            400,
            "invalid_creator_id",
            "creator_id must be a non-empty string.",
        )

    creator_id = creator_id.strip()

    if not isinstance(text, str):
        return reject(
            400,
            "invalid_text",
            "text must be a string.",
            creator_id=creator_id,
        )

    text = text.strip()

    if not text:
        return reject(
            400,
            "empty_text",
            "text cannot be empty.",
            creator_id=creator_id,
        )

    if len(text) > config.MAX_TEXT_CHARS:
        return reject(
            413,
            "text_too_large",
            f"text must be at most {config.MAX_TEXT_CHARS} characters.",
            creator_id=creator_id,
            text_length=len(text),
        )

    if len(stylometry.words(text)) < 3:
        return reject(
            400,
            "text_too_short",
            "text needs at least three words to score.",
            creator_id=creator_id,
        )

    content_id = uuid.uuid4().hex

    try:
        model_score = detector.model_signal(text)
        style_score = stylometry.style_signal(text)
        confidence = scoring.combine_signals(model_score, style_score)
        guess, label = scoring.score_to_label(confidence)
    except detector.DetectorUnavailable as exc:
        return reject(
            503,
            "detector_unavailable",
            str(exc),
            creator_id=creator_id,
            content_id=content_id,
        )
    except ValueError as exc:
        return reject(
            400,
            "unscorable_text",
            str(exc),
            creator_id=creator_id,
            content_id=content_id,
        )

    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=confidence,
        label=label,
        status="decided",
    )

    return jsonify(
        {
            "content_id": content_id,
            "guess": guess,
            "confidence": confidence,
            "label": label,
            "model_score": model_score,
            "style_score": style_score,
            "status": "decided",
        }
    )


@app.post("/appeal")
def appeal():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "error": "invalid_json",
                "message": "Send a JSON object with content_id and reasoning.",
            }
        ), 400

    content_id = payload.get("content_id")
    reasoning = payload.get("reasoning")

    if not isinstance(content_id, str) or not content_id.strip():
        return jsonify(
            {
                "error": "invalid_content_id",
                "message": "content_id must be a non-empty string.",
            }
        ), 400

    if not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify(
            {
                "error": "invalid_reasoning",
                "message": "reasoning must be a non-empty string.",
            }
        ), 400

    content_id = content_id.strip()
    existing = audit.entries_for(content_id)

    if not existing:
        return jsonify(
            {
                "error": "content_not_found",
                "message": "No submission exists with that content_id.",
            }
        ), 404

    original = next(
        (entry for entry in existing if entry.get("creator_id")),
        existing[0],
    )
    creator_id = original.get("creator_id", "unknown")

    audit.log_appeal(
        content_id=content_id,
        creator_id=creator_id,
        reasoning=reasoning.strip(),
    )

    return jsonify(
        {
            "content_id": content_id,
            "status": "under_review",
            "appeal_recorded": True,
            "message": "Your appeal was recorded and the submission is under review.",
        }
    )


@app.get("/log")
def get_log():
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"detector model: {config.DETECTOR_MODEL}")
    print(
        "rate limiting:",
        "ON" if config.RATE_LIMITING_ENABLED else "off (Unit 7)",
    )
    print(f"audit log: {config.AUDIT_LOG}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
