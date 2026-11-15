#!/usr/bin/env python3
"""Run the five committed Unit 9 capstone criteria three times each."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

import requests

import config
import observability

VALID_TEXTS = [
    "I missed the bus this morning and had to walk across campus in the rain before my first class started.",
    "My notes were already organized, so I reviewed the main ideas before class and wrote down two questions for later.",
    "The library was crowded this afternoon, but I found a quiet table upstairs and finished the assignment before dinner.",
    "I usually write short drafts first because it helps me see which parts need more detail before I revise the final version.",
    "The project became easier once I separated the route logic from the scoring functions and tested each part on its own.",
    "I checked the output twice because a small formatting mistake can make a correct result look wrong when someone grades it.",
    "The weather changed quickly today, so I carried my jacket across campus even though the morning started out warm and clear.",
    "I prefer working through one requirement at a time because it makes it easier to notice exactly where a failure begins.",
    "The meeting ended earlier than expected, which gave me enough time to finish my work before heading home for the evening.",
    "I rewrote the explanation after reading it aloud because two sentences sounded awkward and one example needed more context.",
]

REQUIRED_LOG_FIELDS = [
    "timestamp",
    "route",
    "method",
    "status_code",
    "duration_ms",
    "creator_id",
    "input_chars",
    "input_words",
    "output_guess",
    "output_confidence",
]

REQUIRED_RESPONSE_FIELDS = [
    "content_id",
    "guess",
    "confidence",
    "label",
    "model_score",
    "style_score",
    "status",
]


def reset_capstone_log():
    if observability.RUN_LOG.exists():
        observability.RUN_LOG.unlink()


def post_valid(base_url: str, creator_id: str, text: str):
    return requests.post(
        f"{base_url}/submit",
        json={"text": text, "creator_id": creator_id},
        timeout=120,
    )


def criterion_1(base_url: str, trial: int) -> dict:
    reset_capstone_log()

    statuses = []
    for i, text in enumerate(VALID_TEXTS, 1):
        response = post_valid(base_url, f"c1_t{trial}_{i}", text)
        statuses.append(response.status_code)

    rows = [
        row
        for row in observability.read_runs()
        if row.get("route") == "/submit" and row.get("status_code") == 200
    ]

    complete = 0
    missing_by_row = []
    for row in rows:
        missing = [field for field in REQUIRED_LOG_FIELDS if field not in row or row[field] is None]
        if not missing:
            complete += 1
        else:
            missing_by_row.append(
                {
                    "creator_id": row.get("creator_id"),
                    "missing": missing,
                }
            )

    passed = len(rows) == 10 and complete == 10 and all(s == 200 for s in statuses)
    return {
        "passed": passed,
        "summary": f"{complete}/10 successful submissions had every required structured log field",
        "complete_entries": complete,
        "successful_entries": len(rows),
        "http_statuses": statuses,
        "missing_fields": missing_by_row,
    }


def criterion_2(base_url: str, trial: int) -> dict:
    reset_capstone_log()

    statuses = []
    for i, text in enumerate(VALID_TEXTS, 1):
        response = post_valid(base_url, f"c2_t{trial}_{i}", text)
        statuses.append(response.status_code)

    response = requests.get(f"{base_url}/metrics", timeout=30)
    metrics = response.json()

    submit_requests = metrics.get("submit_requests")
    successful = metrics.get("successful_submits")
    label_total = sum((metrics.get("label_counts") or {}).values())

    passed = (
        response.status_code == 200
        and submit_requests == 10
        and successful == 10
        and label_total == 10
        and all(s == 200 for s in statuses)
    )

    return {
        "passed": passed,
        "summary": (
            f"metrics reported {submit_requests} submits, "
            f"{successful} successful, label total {label_total}"
        ),
        "metrics": metrics,
        "http_statuses": statuses,
    }


def criterion_3(base_url: str, trial: int) -> dict:
    reset_capstone_log()

    bodies = [
        ("empty_text", {"text": "", "creator_id": f"c3_t{trial}_empty"}),
        ("missing_text", {"creator_id": f"c3_t{trial}_missing"}),
        ("null_text", {"text": None, "creator_id": f"c3_t{trial}_null"}),
        (
            "too_large",
            {"text": "word " * 5000, "creator_id": f"c3_t{trial}_large"},
        ),
    ]

    responses = []
    for name, body in bodies:
        response = requests.post(
            f"{base_url}/submit",
            json=body,
            timeout=30,
        )
        responses.append(
            {
                "case": name,
                "status_code": response.status_code,
                "body": response.json(),
            }
        )

    rows = [row for row in observability.read_runs() if row.get("route") == "/submit"]

    logged_failures = [
        row
        for row in rows
        if 400 <= int(row.get("status_code", 0)) < 500
        and row.get("output_error")
    ]

    correct_statuses = all(
        400 <= item["status_code"] < 500 for item in responses
    )

    passed = correct_statuses and len(logged_failures) == 4

    return {
        "passed": passed,
        "summary": (
            f"{sum(1 for x in responses if 400 <= x['status_code'] < 500)}/4 "
            f"returned 4xx and {len(logged_failures)}/4 were logged with errors"
        ),
        "responses": responses,
        "logged_failures": logged_failures,
    }


def criterion_4(base_url: str, trial: int) -> dict:
    reset_capstone_log()

    warmup = post_valid(
        base_url,
        f"c4_t{trial}_warmup",
        VALID_TEXTS[0],
    )

    durations = []
    statuses = []

    for i, text in enumerate(VALID_TEXTS, 1):
        started = time.perf_counter()
        response = post_valid(base_url, f"c4_t{trial}_{i}", text)
        elapsed = time.perf_counter() - started
        durations.append(elapsed)
        statuses.append(response.status_code)

    under_500 = sum(1 for value in durations if value < 0.500)
    passed = (
        warmup.status_code == 200
        and under_500 >= 9
        and all(s == 200 for s in statuses)
    )

    return {
        "passed": passed,
        "summary": f"{under_500}/10 warm submissions completed under 500 ms",
        "warmup_status": warmup.status_code,
        "durations_seconds": [round(x, 4) for x in durations],
        "http_statuses": statuses,
    }


def criterion_5(base_url: str, trial: int) -> dict:
    reset_capstone_log()

    details = []

    for i, text in enumerate(VALID_TEXTS, 1):
        response = post_valid(base_url, f"c5_t{trial}_{i}", text)

        try:
            body = response.json()
        except ValueError:
            body = {}

        missing = [
            field
            for field in REQUIRED_RESPONSE_FIELDS
            if field not in body
        ]

        details.append(
            {
                "status_code": response.status_code,
                "missing_fields": missing,
            }
        )

    complete = sum(
        1
        for item in details
        if item["status_code"] == 200 and not item["missing_fields"]
    )

    passed = complete == 10

    return {
        "passed": passed,
        "summary": f"{complete}/10 returned HTTP 200 with every required original response field",
        "complete_responses": complete,
        "responses": details,
    }


CRITERIA = [
    {
        "number": 1,
        "name": "Every successful submission creates a complete structured log entry",
        "target": "10 of 10 complete structured log entries",
        "runner": criterion_1,
    },
    {
        "number": 2,
        "name": "The metrics endpoint matches known request activity",
        "target": "10 submits, 10 successes, label counts total 10",
        "runner": criterion_2,
    },
    {
        "number": 3,
        "name": "Failed requests are observable",
        "target": "4 of 4 return 4xx and are logged with status and error",
        "runner": criterion_3,
    },
    {
        "number": 4,
        "name": "Warm submission latency stays under 500 milliseconds",
        "target": "At least 9 of 10 under 500 ms after warm-up",
        "runner": criterion_4,
    },
    {
        "number": 5,
        "name": "The observability extension does not break the original submission path",
        "target": "10 of 10 HTTP 200 with all required response fields",
        "runner": criterion_5,
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["before", "after"])
    parser.add_argument(
        "--url",
        default=f"http://{config.HOST}:{config.PORT}",
    )
    args = parser.parse_args()

    try:
        health = requests.get(f"{args.url}/health", timeout=10)
        health.raise_for_status()
    except requests.RequestException:
        raise SystemExit(
            f"Nothing answering at {args.url}. Start python capstone_app.py first."
        )

    print(f"Capstone evaluation: {args.label}")
    print(f"Service: {args.url}")
    print("5 criteria x 3 trials")
    print()

    output = {
        "label": args.label,
        "service": args.url,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "producer": "run_capstone_eval.py",
        "criteria": [],
    }

    for item in CRITERIA:
        print(f"Criterion {item['number']}: {item['name']}")
        trials = []

        for trial in range(1, 4):
            result = item["runner"](args.url, trial)
            trials.append(result)
            verdict = "PASS" if result["passed"] else "FAIL"
            print(f"  run {trial}: {result['summary']} => {verdict}")

        met = all(trial["passed"] for trial in trials)
        print(f"  verdict: {'MET' if met else 'MISSED'}")
        print()

        output["criteria"].append(
            {
                "criterion": item["number"],
                "name": item["name"],
                "target": item["target"],
                "trials": trials,
                "verdict": "MET" if met else "MISSED",
            }
        )

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    json_path = config.RESULTS_DIR / f"capstone_eval_{stamp}_{args.label}.json"
    md_path = config.RESULTS_DIR / f"capstone_eval_{stamp}_{args.label}.md"

    json_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = [
        f"# Capstone Evaluation: {args.label.title()}",
        "",
        "Produced by `run_capstone_eval.py`.",
        "",
        "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
        "|---|---|---|---|---|---|",
    ]

    for item in output["criteria"]:
        summaries = [trial["summary"] for trial in item["trials"]]
        md.append(
            f"| {item['criterion']}. {item['name']} | {item['target']} | "
            f"{summaries[0]} | {summaries[1]} | {summaries[2]} | "
            f"{item['verdict']} |"
        )

    md += ["", "## Real output", ""]

    for item in output["criteria"]:
        md.append(f"### Criterion {item['criterion']}")
        md.append("")
        for index, trial in enumerate(item["trials"], 1):
            md.append(f"**Run {index}:** `{trial['summary']}`")
        md.append("")
        md.append("```json")
        md.append(json.dumps(item["trials"][0], indent=2, ensure_ascii=False))
        md.append("```")
        md.append("")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print("Verdicts:")
    for item in output["criteria"]:
        print(f"  Criterion {item['criterion']}: {item['verdict']}")

    print()
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
