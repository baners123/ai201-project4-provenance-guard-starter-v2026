# Capstone Evaluation: After

Produced by `run_capstone_eval.py`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every successful submission creates a complete structured log entry | 10 of 10 complete structured log entries | 10/10 successful submissions had every required structured log field | 10/10 successful submissions had every required structured log field | 10/10 successful submissions had every required structured log field | MET |
| 2. The metrics endpoint matches known request activity | 10 submits, 10 successes, label counts total 10 | metrics reported 10 submits, 10 successful, label total 10 | metrics reported 10 submits, 10 successful, label total 10 | metrics reported 10 submits, 10 successful, label total 10 | MET |
| 3. Failed requests are observable | 4 of 4 return 4xx and are logged with status and error | 4/4 returned 4xx and 4/4 were logged with errors | 4/4 returned 4xx and 4/4 were logged with errors | 4/4 returned 4xx and 4/4 were logged with errors | MET |
| 4. Warm submission latency stays under 500 milliseconds | At least 9 of 10 under 500 ms after warm-up | 10/10 warm submissions completed under 500 ms | 10/10 warm submissions completed under 500 ms | 10/10 warm submissions completed under 500 ms | MET |
| 5. The observability extension does not break the original submission path | 10 of 10 HTTP 200 with all required response fields | 10/10 returned HTTP 200 with every required original response field | 10/10 returned HTTP 200 with every required original response field | 10/10 returned HTTP 200 with every required original response field | MET |

## Real output

### Criterion 1

**Run 1:** `10/10 successful submissions had every required structured log field`
**Run 2:** `10/10 successful submissions had every required structured log field`
**Run 3:** `10/10 successful submissions had every required structured log field`

```json
{
  "passed": true,
  "summary": "10/10 successful submissions had every required structured log field",
  "complete_entries": 10,
  "successful_entries": 10,
  "http_statuses": [
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200
  ],
  "missing_fields": []
}
```

### Criterion 2

**Run 1:** `metrics reported 10 submits, 10 successful, label total 10`
**Run 2:** `metrics reported 10 submits, 10 successful, label total 10`
**Run 3:** `metrics reported 10 submits, 10 successful, label total 10`

```json
{
  "passed": true,
  "summary": "metrics reported 10 submits, 10 successful, label total 10",
  "metrics": {
    "average_submit_duration_ms": 43.68,
    "error_counts": {},
    "label_counts": {
      "ai": 2,
      "unsure": 8
    },
    "last_run_timestamp": "2026-11-15T19:53:56.604+00:00",
    "p95_submit_duration_ms": 46.14,
    "rejected_or_failed_requests": 0,
    "run_log": "/Users/jimiadegoroye/Desktop/ai201-project4-provenance-guard-starter-v2026/logs/capstone_runs.jsonl",
    "submit_requests": 10,
    "successful_submits": 10,
    "total_requests_logged": 10
  },
  "http_statuses": [
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200
  ]
}
```

### Criterion 3

**Run 1:** `4/4 returned 4xx and 4/4 were logged with errors`
**Run 2:** `4/4 returned 4xx and 4/4 were logged with errors`
**Run 3:** `4/4 returned 4xx and 4/4 were logged with errors`

```json
{
  "passed": true,
  "summary": "4/4 returned 4xx and 4/4 were logged with errors",
  "responses": [
    {
      "case": "empty_text",
      "status_code": 400,
      "body": {
        "error": "empty_text",
        "message": "text cannot be empty."
      }
    },
    {
      "case": "missing_text",
      "status_code": 400,
      "body": {
        "error": "invalid_text",
        "message": "text must be a string."
      }
    },
    {
      "case": "null_text",
      "status_code": 400,
      "body": {
        "error": "invalid_text",
        "message": "text must be a string."
      }
    },
    {
      "case": "too_large",
      "status_code": 413,
      "body": {
        "error": "text_too_large",
        "message": "text must be at most 20000 characters."
      }
    }
  ],
  "logged_failures": [
    {
      "timestamp": "2026-11-15T19:53:58.207+00:00",
      "method": "POST",
      "route": "/submit",
      "status_code": 400,
      "duration_ms": 0.43,
      "creator_id": "c3_t1_empty",
      "input_preview": "",
      "input_chars": 0,
      "input_words": 0,
      "output_guess": null,
      "output_confidence": null,
      "output_status": null,
      "output_error": "empty_text"
    },
    {
      "timestamp": "2026-11-15T19:53:58.210+00:00",
      "method": "POST",
      "route": "/submit",
      "status_code": 400,
      "duration_ms": 0.24,
      "creator_id": "c3_t1_missing",
      "output_guess": null,
      "output_confidence": null,
      "output_status": null,
      "output_error": "invalid_text"
    },
    {
      "timestamp": "2026-11-15T19:53:58.215+00:00",
      "method": "POST",
      "route": "/submit",
      "status_code": 400,
      "duration_ms": 0.33,
      "creator_id": "c3_t1_null",
      "input_preview": "None",
      "input_chars": null,
      "input_words": null,
      "output_guess": null,
      "output_confidence": null,
      "output_status": null,
      "output_error": "invalid_text"
    },
    {
      "timestamp": "2026-11-15T19:53:58.226+00:00",
      "method": "POST",
      "route": "/submit",
      "status_code": 413,
      "duration_ms": 2.0,
      "creator_id": "c3_t1_large",
      "input_preview": "word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word ",
      "input_chars": 24999,
      "input_words": 5000,
      "output_guess": null,
      "output_confidence": null,
      "output_status": null,
      "output_error": "text_too_large"
    }
  ]
}
```

### Criterion 4

**Run 1:** `10/10 warm submissions completed under 500 ms`
**Run 2:** `10/10 warm submissions completed under 500 ms`
**Run 3:** `10/10 warm submissions completed under 500 ms`

```json
{
  "passed": true,
  "summary": "10/10 warm submissions completed under 500 ms",
  "warmup_status": 200,
  "durations_seconds": [
    0.2275,
    0.0938,
    0.0513,
    0.065,
    0.045,
    0.0445,
    0.0466,
    0.0483,
    0.0557,
    0.0488
  ],
  "http_statuses": [
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200,
    200
  ]
}
```

### Criterion 5

**Run 1:** `10/10 returned HTTP 200 with every required original response field`
**Run 2:** `10/10 returned HTTP 200 with every required original response field`
**Run 3:** `10/10 returned HTTP 200 with every required original response field`

```json
{
  "passed": true,
  "summary": "10/10 returned HTTP 200 with every required original response field",
  "complete_responses": 10,
  "responses": [
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    },
    {
      "status_code": 200,
      "missing_fields": []
    }
  ]
}
```
