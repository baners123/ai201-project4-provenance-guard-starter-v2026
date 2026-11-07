#!/usr/bin/env python3
"""
Run all five Unit 8 Provenance Guard criteria three times.

Usage:
    python app.py
    python run_eval.py --label before

After exactly one improvement:
    python run_eval.py --label after

This evaluator calculates the verdicts for the five criteria in criteria.md and
writes both JSON and markdown evidence into results/.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import config
import scenarios


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def request_json(requests, method, url, **kwargs):
    response = requests.request(method, url, timeout=90, **kwargs)
    try:
        payload = response.json() if response.content else {}
    except Exception:
        payload = {"_non_json": response.text[:500]}
    return response.status_code, payload


def get_log(requests, base_url):
    status, payload = request_json(requests, "GET", f"{base_url}/log")
    if status != 200:
        return []
    return payload.get("entries", [])


def find_appeal(entries, content_id):
    return any(
        entry.get("content_id") == content_id
        and entry.get("event") == "appeal"
        and entry.get("status") == "under_review"
        for entry in entries
    )


def find_rejection(entries, creator_id):
    return any(
        entry.get("creator_id") == creator_id
        and entry.get("event") == "rejected"
        for entry in entries
    )


def submit_text(requests, base_url, text, creator_id):
    status, payload = request_json(
        requests,
        "POST",
        f"{base_url}/submit",
        json={"text": text, "creator_id": creator_id},
    )
    return {
        "status": status,
        "guess": payload.get("guess"),
        "confidence": payload.get("confidence"),
        "model_score": payload.get("model_score"),
        "style_score": payload.get("style_score"),
        "label": payload.get("label"),
        "content_id": payload.get("content_id"),
        "payload": payload,
    }


def criterion_1(requests, base_url, trial):
    results = []
    for i, text in enumerate(scenarios.load_my_writing(), 1):
        results.append(
            submit_text(
                requests,
                base_url,
                text,
                f"eval_c1_t{trial}_{i}",
            )
        )

    ai_flags = sum(r.get("guess") == "ai" for r in results)
    return {
        "metric": f"{ai_flags}/10 flagged high-confidence AI",
        "value": ai_flags,
        "passed": ai_flags <= 1,
        "results": results,
    }


def criterion_2(requests, base_url, trial):
    human_scores = []
    ai_scores = []
    results = []

    for i, text in enumerate(scenarios.load_my_writing()[:5], 1):
        result = submit_text(
            requests,
            base_url,
            text,
            f"eval_c2_h_t{trial}_{i}",
        )
        results.append({"group": "human", **result})
        if result.get("confidence") is not None:
            human_scores.append(float(result["confidence"]))

    for i, text in enumerate(scenarios.AI_SAMPLES, 1):
        result = submit_text(
            requests,
            base_url,
            text,
            f"eval_c2_a_t{trial}_{i}",
        )
        results.append({"group": "ai", **result})
        if result.get("confidence") is not None:
            ai_scores.append(float(result["confidence"]))

    human_avg = sum(human_scores) / len(human_scores) if human_scores else None
    ai_avg = sum(ai_scores) / len(ai_scores) if ai_scores else None
    gap = (ai_avg - human_avg) if human_avg is not None and ai_avg is not None else None

    passed = gap is not None and gap >= 0.20

    return {
        "metric": (
            f"AI avg {ai_avg:.4f}, human avg {human_avg:.4f}, gap {gap:.4f}"
            if gap is not None
            else "could not calculate score gap"
        ),
        "value": gap,
        "human_average": human_avg,
        "ai_average": ai_avg,
        "passed": passed,
        "results": results,
    }


def criterion_3(requests, base_url, trial):
    results = []
    for i, text in enumerate(scenarios.calibration_texts(), 1):
        results.append(
            submit_text(
                requests,
                base_url,
                text,
                f"eval_c3_t{trial}_{i}",
            )
        )

    guesses = sorted({r.get("guess") for r in results if r.get("guess")})
    passed = set(guesses) == {"ai", "human", "unsure"}

    return {
        "metric": f"{len(guesses)}/3 labels reached: {', '.join(guesses) or 'none'}",
        "value": len(guesses),
        "passed": passed,
        "results": results,
    }


def criterion_4(requests, base_url, trial):
    results = []
    successful = 0

    for i, text in enumerate(scenarios.load_my_writing()[:5], 1):
        submission = submit_text(
            requests,
            base_url,
            text,
            f"eval_c4_t{trial}_{i}",
        )
        content_id = submission.get("content_id")

        appeal_status = None
        appeal_payload = {}
        logged = False

        if content_id:
            appeal_status, appeal_payload = request_json(
                requests,
                "POST",
                f"{base_url}/appeal",
                json={
                    "content_id": content_id,
                    "reasoning": "I believe this decision should be reviewed.",
                },
            )
            logged = find_appeal(get_log(requests, base_url), content_id)

        ok = (
            appeal_status == 200
            and appeal_payload.get("status") == "under_review"
            and appeal_payload.get("appeal_recorded") is True
            and logged
        )

        if ok:
            successful += 1

        results.append(
            {
                "submission": submission,
                "appeal_status": appeal_status,
                "appeal": appeal_payload,
                "appeal_in_log": logged,
                "passed": ok,
            }
        )

    return {
        "metric": f"{successful}/5 appeals moved to under_review and were logged",
        "value": successful,
        "passed": successful == 5,
        "results": results,
    }


def criterion_5(requests, base_url, trial):
    results = []
    successful = 0

    for i, body in enumerate(scenarios.BAD_INPUT_BODIES, 1):
        body = dict(body)
        creator_id = body.get("creator_id", f"eval_c5_t{trial}_{i}")
        if "creator_id" in body:
            body["creator_id"] = f"{creator_id}_t{trial}"

        status, payload = request_json(
            requests,
            "POST",
            f"{base_url}/submit",
            json=body,
        )

        actual_creator = body.get("creator_id", "unknown")
        logged = find_rejection(get_log(requests, base_url), actual_creator)

        ok = 400 <= status < 500 and status != 429 and logged
        if ok:
            successful += 1

        results.append(
            {
                "sent": {
                    key: ("<very long text>" if key == "text" and isinstance(value, str) and len(value) > 200 else value)
                    for key, value in body.items()
                },
                "status": status,
                "payload": payload,
                "rejection_in_log": logged,
                "passed": ok,
            }
        )

    return {
        "metric": f"{successful}/4 bad inputs returned safe 4xx JSON and were logged",
        "value": successful,
        "passed": successful == 4,
        "results": results,
    }


CRITERIA = [
    {
        "number": 1,
        "name": "False positives on my own writing",
        "target": "<= 1 of 10 high-confidence AI",
        "runner": criterion_1,
    },
    {
        "number": 2,
        "name": "AI and human calibration scores are separated",
        "target": "AI average - human average >= 0.20",
        "runner": criterion_2,
    },
    {
        "number": 3,
        "name": "All three labels are reachable",
        "target": "3 of 3 labels",
        "runner": criterion_3,
    },
    {
        "number": 4,
        "name": "Valid appeals move to review and are recorded",
        "target": "5 of 5",
        "runner": criterion_4,
    },
    {
        "number": 5,
        "name": "Bad input fails safely",
        "target": "4 of 4",
        "runner": criterion_5,
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()

    problems = scenarios.validate()
    if problems:
        print("Cannot run yet:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)

    if args.trials < 3:
        print("Unit 8 requires three trials.", file=sys.stderr)
        sys.exit(1)

    try:
        import requests
    except ImportError:
        print("Install requirements first: pip install -r requirements.txt")
        sys.exit(1)

    try:
        health = requests.get(f"{args.url}/health", timeout=5)
        health.raise_for_status()
    except Exception:
        print(f"Nothing answering at {args.url}. Start python app.py first.")
        sys.exit(1)

    run_data = []

    for criterion in CRITERIA:
        print(f"\nCriterion {criterion['number']}: {criterion['name']}")
        trials = []

        for trial in range(1, args.trials + 1):
            result = criterion["runner"](requests, args.url, trial)
            trials.append(result)
            print(
                f"  run {trial}: {result['metric']} "
                f"=> {'PASS' if result['passed'] else 'FAIL'}"
            )

        verdict = "MET" if all(t["passed"] for t in trials) else "MISSED"
        run_data.append(
            {
                "criterion": criterion["number"],
                "name": criterion["name"],
                "target": criterion["target"],
                "trials": trials,
                "verdict": verdict,
            }
        )

    write_results(run_data, args)


def write_results(run_data, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = args.label or "run"

    json_path = config.RESULTS_DIR / f"eval_{stamp}_{label}.json"
    md_path = config.RESULTS_DIR / f"eval_{stamp}_{label}.md"

    payload = {
        "label": label,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "service": f"http://{config.HOST}:{config.PORT}",
        "criteria": run_data,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Unit 8 Run Log - {label}",
        "",
        "- Produced by: `run_eval.py`",
        "- Service route: `app.py::submit`",
        "- Appeal route: `app.py::appeal`",
        "- Audit source: `logs/audit.jsonl` through `GET /log`",
        "- Three trials per criterion",
        "",
        "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
        "|---|---|---|---|---|---|",
    ]

    for row in run_data:
        metrics = [trial["metric"].replace("|", "/") for trial in row["trials"]]
        lines.append(
            f"| {row['criterion']}. {row['name']} | {row['target']} | "
            f"{metrics[0]} | {metrics[1]} | {metrics[2]} | {row['verdict']} |"
        )

    lines += ["", "## Real output", ""]

    for row in run_data:
        lines += [
            f"### Criterion {row['criterion']}: {row['name']}",
            "",
        ]
        for i, trial in enumerate(row["trials"], 1):
            lines += [
                f"**Run {i}: {trial['metric']}**",
                "",
                "```json",
                json.dumps(trial["results"], indent=2),
                "```",
                "",
            ]

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    print("\nVerdicts:")
    for row in run_data:
        print(f"  Criterion {row['criterion']}: {row['verdict']}")


if __name__ == "__main__":
    main()
