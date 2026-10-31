"""Configuration for Provenance Guard."""

import os
from pathlib import Path

ROOT = Path(__file__).parent

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")

# Local detector
DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")
DETECTOR_MAX_TOKENS = 400

# Unit 7 scoring
# The model signal gets more weight because it reads token predictability.
# The style signal is useful but easier to manipulate with formatting edits.
WEIGHT_MODEL_SIGNAL = 0.65
WEIGHT_STYLE_SIGNAL = 0.35

# A wide unsure band is intentional because a false accusation is the costly error.
HUMAN_THRESHOLD = 0.30
AI_THRESHOLD = 0.75

# Input validation
MAX_TEXT_CHARS = 20_000

# Unit 8 rate limiting
# Keep this False for Unit 7. Turn it on in Unit 8 Milestone 1.
RATE_LIMITING_ENABLED = True

# Chosen Unit 8 limits. Eight submissions in a minute is enough for a real writer
# retrying work, but a 15-request flood will clearly trigger 429 responses.
RATE_LIMIT_PER_MINUTE = 8
RATE_LIMIT_PER_DAY = 100
RATE_LIMIT_STORAGE = "memory://"

# Paths
LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
