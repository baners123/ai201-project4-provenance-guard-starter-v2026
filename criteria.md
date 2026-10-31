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
