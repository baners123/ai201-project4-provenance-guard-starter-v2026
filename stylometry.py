"""Signal two for Provenance Guard: simple text-shape measurements."""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split text into rough sentences."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part for part in parts if part.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words with punctuation removed."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _clip01(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def sentence_length_spread(text: str) -> float:
    """Coefficient of variation of sentence lengths.

    Higher values mean sentence lengths vary more.
    """
    parts = sentences(text)
    lengths = [len(words(part)) for part in parts if words(part)]

    if len(lengths) < 2:
        return 0.0

    mean = statistics.mean(lengths)
    if mean <= 0:
        return 0.0

    return round(statistics.stdev(lengths) / mean, 4)


def type_token_ratio(text: str) -> float:
    """Unique words divided by total words."""
    tokens = words(text)
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)


def punctuation_density(text: str) -> float:
    """Interesting punctuation marks per word.

    The measure intentionally ignores ordinary periods because commas,
    semicolons, colons, parentheses, question marks, and exclamation marks
    vary more between writers.
    """
    token_count = len(words(text))
    if token_count == 0:
        return 0.0

    punctuation_count = len(re.findall(r"[,;:!?()\"']", text))
    return round(punctuation_count / token_count, 4)


def style_signal(text: str) -> float:
    """Return a 0 to 1 score where higher means more AI-like.

    The three raw measures point toward human variation when they are high,
    so each is normalized to a human-like score and then inverted.
    """
    spread = sentence_length_spread(text)
    ttr = type_token_ratio(text)
    punctuation = punctuation_density(text)

    # These are simple normalization bands, not claims about authorship.
    spread_human = _clip01(spread / 0.75)
    vocabulary_human = _clip01((ttr - 0.35) / 0.45)
    punctuation_human = _clip01(punctuation / 0.25)

    human_style = (
        0.40 * spread_human
        + 0.35 * vocabulary_human
        + 0.25 * punctuation_human
    )

    return round(_clip01(1.0 - human_style), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "I missed the bus this morning, which was annoying. "
        "Then it started raining. By the time I reached class, my notes "
        "were damp, my coffee was cold, and I had completely forgotten "
        "the question I wanted to ask."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words")
    print(f"sentence_length_spread {sentence_length_spread(text)}")
    print(f"type_token_ratio {type_token_ratio(text)}")
    print(f"punctuation_density {punctuation_density(text)}")
    print(f"style_signal {style_signal(text)} (higher = more likely AI)")
