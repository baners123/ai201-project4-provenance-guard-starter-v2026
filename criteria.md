# Acceptance Criteria: Provenance Guard

## 1. False positives on my own writing

When I submit 10 pieces of writing that I wrote myself, at most 1 of the 10 may be labeled `high-confidence AI`.

**Why this target:** A false positive is the most expensive mistake in this service because it accuses a real writer of using AI. I am willing to let more uncertain cases fall into the unsure range if that keeps the high-confidence AI label rare on real human writing.

## 2. AI and human calibration scores are separated

For 5 clearly AI-generated calibration samples and 5 clearly human-written calibration samples selected before evaluation, the average combined score for the AI group should be at least 0.20 higher than the average combined score for the human group.

**Why this target:** The service combines a model signal and a stylometry signal, so the combined score should create a noticeable separation between the two groups instead of clustering everything near the same threshold. A 0.20 gap is large enough to show that the two-signal design is contributing useful separation.

## 3. All three labels are reachable

Across 6 deliberately chosen calibration inputs that span the expected score range, the service must produce all 3 reader-facing labels at least once: high-confidence human, unsure, and high-confidence AI.

**Why this target:** My thresholds are 0.30 and 0.75. If one of the three labels can never be reached, then the threshold design is not functioning as intended and the uncertainty layer is not actually available to users.

## 4. Every valid appeal moves the item to review and is recorded

For 5 valid appeals using real existing `content_id` values, all 5 must return `status: under_review`, and all 5 must create an appeal entry in `logs/audit.jsonl`.

**Why this target:** The appeal path is the writer's protection when the detector is wrong. Because a false accusation can harm a real writer, a valid appeal should never silently fail or leave the original decision as the final status.

## 5. Bad input fails safely

For 4 bad-input cases, missing `text`, empty `text`, `null` text, and text longer than 20,000 characters, all 4 requests must return a 4xx JSON response, none may return a 500 error, and each rejection must be written to the audit log.

**Why this target:** Invalid input should be stopped at the route before either signal runs. This protects the detector pipeline from malformed requests and makes failures visible in the audit log instead of turning them into unexplained crashes.

The Improvement

I changed the high-confidence AI threshold from 0.75 to 0.62.

The before evaluation showed that Criterion 3 failed in all three trials because none of the calibration inputs reached the AI label. The strongest AI calibration sample scored 0.6497, while the other AI sample scored 0.6004. The human and borderline examples remained substantially lower.

I chose 0.62 because it was a small change that allowed the 0.6497 AI sample to reach the high-confidence AI label while keeping the 0.6004 sample in the unsure range. I did not change either signal or the 65% model and 35% stylometry weighting.

The tradeoff is that lowering the AI threshold may increase false positives. I therefore reran all five acceptance criteria after the change to check whether Criterion 1 still protected human writing.


# Unit 9 Capstone Acceptance Criteria

## 1. Every successful submission creates a complete structured log entry

For 10 valid `/submit` requests, all 10 must create an entry in `logs/capstone_runs.jsonl` containing a timestamp, route, HTTP method, status code, duration in milliseconds, creator ID, input character count, input word count, output guess, and output confidence.

**Why this target:** The main capstone extension is observability. A request that succeeds but does not leave enough structured information to explain what happened defeats the purpose of the extension. I chose 10 out of 10 because missing operational records would make later diagnosis unreliable.

## 2. The metrics endpoint matches known request activity

After starting from a known log state and sending 10 valid submissions, the `/metrics` endpoint must report 10 submit requests and 10 successful submissions. Its label counts must also add up to 10.

**Why this target:** The metrics endpoint should summarize the structured log accurately rather than give approximate numbers. Because I control exactly how many requests are sent during the test, the expected count is known and there should be no difference between the test activity and the reported totals.

## 3. Failed requests are observable

For 4 invalid submission requests, including empty text, missing text, null text, and text longer than 20,000 characters, all 4 must return a 4xx response and all 4 must create structured entries in `logs/capstone_runs.jsonl` with the correct HTTP status and an error value.

**Why this target:** Failed requests are especially important to observe because otherwise they appear only as missing successful results. I chose all 4 because the extension should record both successful and rejected requests consistently.

## 4. Warm submission latency stays under 500 milliseconds

After one warm-up request has loaded the local model, at least 9 of 10 valid `/submit` requests must complete in under 500 milliseconds according to the end-to-end timing measured by the client.

**Why this target:** The first request can be much slower because the local GPT-2 model has to load, so I exclude the warm-up request. A 500 millisecond target gives the local service room for normal variation while still identifying major slowdowns in repeated use.

## 5. The observability extension does not break the original submission path

For 10 valid submissions, all 10 must return HTTP 200 and include `content_id`, `guess`, `confidence`, `label`, `model_score`, `style_score`, and `status` in the JSON response while the capstone logging extension is enabled.

**Why this target:** The capstone should add observability without breaking the system it extends. I chose 10 out of 10 because instrumentation should not introduce intermittent failures into the original submission path.