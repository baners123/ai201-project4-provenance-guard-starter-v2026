#!/usr/bin/env python3
"""Measure ten real local Provenance Guard runs."""

from __future__ import annotations

import argparse
import datetime as dt
import statistics
import time

import requests
import config

DEFAULT_TEXT = (
    "I wrote this paragraph to measure how long the local Provenance Guard "
    "service takes to score one ordinary submission. The wording stays the "
    "same across runs so the timing comparison measures the system rather "
    "than changes in the input."
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    args = parser.parse_args()

    for i in range(args.warmup):
        response = requests.post(
            f"{args.url}/submit",
            json={"text": args.text, "creator_id": f"capstone_warmup_{i + 1}"},
            timeout=120,
        )
        print(f"warm-up {i + 1}: HTTP {response.status_code}")

    durations = []
    statuses = []
    for i in range(args.runs):
        started = time.perf_counter()
        response = requests.post(
            f"{args.url}/submit",
            json={"text": args.text, "creator_id": f"capstone_cost_{i + 1}"},
            timeout=120,
        )
        seconds = time.perf_counter() - started
        durations.append(seconds)
        statuses.append(response.status_code)
        print(f"run {i + 1}: {seconds:.4f}s, HTTP {response.status_code}")

    avg = statistics.mean(durations)
    median = statistics.median(durations)

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"capstone_cost_{stamp}.md"

    lines = [
        "# Capstone Cost Measurement", "",
        f"- Warm-up runs excluded: {args.warmup}",
        f"- Measured runs: {args.runs}",
        f"- Average local round-trip time: {avg:.4f} seconds",
        f"- Median local round-trip time: {median:.4f} seconds",
        f"- HTTP statuses: {' '.join(str(s) for s in statuses)}", "",
        "## Per-run timings", "",
    ]
    lines.extend(f"- Run {i}: {seconds:.4f} seconds" for i, seconds in enumerate(durations, 1))
    lines += [
        "", "## 100 runs per day", "",
        f"{avg:.4f} seconds/run x 100 runs = {avg * 100:.2f} seconds of local compute time per day.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"Average: {avg:.4f}s")
    print(f"Median:  {median:.4f}s")
    print(f"100 runs/day: {avg * 100:.2f}s")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
