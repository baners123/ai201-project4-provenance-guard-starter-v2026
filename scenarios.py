"""
Unit 8 evaluation inputs for the five Provenance Guard criteria.

The only file you must supply yourself is data/my_writing.txt because
Criterion 1 explicitly tests writing that YOU wrote.

Format data/my_writing.txt as 10 pieces separated by a line containing:
---
"""

from pathlib import Path

ROOT = Path(__file__).parent
MY_WRITING_FILE = ROOT / "data" / "my_writing.txt"


AI_SAMPLES = [
    (
        "The advancement of artificial intelligence has transformed modern "
        "communication by increasing efficiency, improving access to information, "
        "and enabling organizations to automate repetitive tasks. As these systems "
        "continue to develop, responsible implementation will remain essential to "
        "ensuring that their benefits are distributed fairly across society."
    ),
    (
        "Effective leadership requires clear communication, strategic planning, "
        "and the ability to adapt to changing circumstances. Leaders who establish "
        "measurable goals and encourage collaboration can improve organizational "
        "performance while creating an environment in which employees feel valued."
    ),
    (
        "Climate change presents a complex global challenge that requires cooperation "
        "between governments, businesses, and individuals. Investments in renewable "
        "energy, efficient infrastructure, and scientific research can reduce emissions "
        "while supporting long-term economic development."
    ),
    (
        "Education plays a critical role in preparing individuals for a rapidly "
        "changing workforce. By combining technical knowledge with communication, "
        "problem-solving, and teamwork, schools can help students build skills that "
        "remain useful across different careers and industries."
    ),
    (
        "Financial planning is most effective when individuals establish realistic "
        "goals, monitor their spending, and make consistent decisions over time. "
        "Creating a budget, maintaining emergency savings, and understanding risk can "
        "provide a stronger foundation for long-term financial stability."
    ),
]


BORDERLINE_SAMPLES = [
    (
        "I keep rewriting this paragraph because every version sounds too polished. "
        "The basic point is simple: I like technology when it saves me time, but I "
        "get suspicious when people act like a score from a model settles an argument. "
        "Sometimes the number helps. Sometimes it just gives the uncertainty a decimal."
    ),
    (
        "A reliable system should communicate what it knows and what it does not know. "
        "That sounds obvious, although it becomes harder when a prediction affects a "
        "real person. I would rather review a questionable result than pretend a weak "
        "signal is stronger evidence than it actually is."
    ),
]


BAD_INPUT_BODIES = [
    {"creator_id": "eval_bad_missing"},
    {"text": "", "creator_id": "eval_bad_empty"},
    {"text": None, "creator_id": "eval_bad_null"},
    {"text": "word " * 5000, "creator_id": "eval_bad_huge"},
]


def load_my_writing() -> list[str]:
    if not MY_WRITING_FILE.exists():
        return []

    raw = MY_WRITING_FILE.read_text(encoding="utf-8")
    pieces = [piece.strip() for piece in raw.split("\n---\n") if piece.strip()]
    return pieces


def calibration_texts() -> list[str]:
    human = load_my_writing()
    if len(human) < 2:
        return []
    return [
        human[0],
        human[1],
        AI_SAMPLES[0],
        AI_SAMPLES[1],
        BORDERLINE_SAMPLES[0],
        BORDERLINE_SAMPLES[1],
    ]


def validate() -> list[str]:
    problems = []
    human = load_my_writing()

    if len(human) != 10:
        problems.append(
            "data/my_writing.txt must contain exactly 10 pieces separated by a line "
            "containing ---"
        )

    for i, text in enumerate(human, 1):
        if len(text.split()) < 20:
            problems.append(
                f"my writing piece {i} has fewer than 20 words; use a real paragraph "
                "so the detector has enough text to evaluate"
            )

    if len(AI_SAMPLES) != 5:
        problems.append("AI_SAMPLES must contain exactly 5 samples")

    if len(calibration_texts()) != 6 and len(human) == 10:
        problems.append("Criterion 3 needs exactly 6 calibration inputs")

    if len(BAD_INPUT_BODIES) != 4:
        problems.append("Criterion 5 needs exactly 4 bad-input bodies")

    return problems
