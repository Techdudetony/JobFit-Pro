# core/processor/ai_detector.py
"""
AI Detection Scorer — JobFit Pro
----------------------------------

Two modes:
1. Heuristic (instant) — pattern matching for common AI writing signals
2. Deep analysis (OpenAI) — sends resume to GPT for probabilistic AI detection

Returns a score 0-100 where 100 = almost certainly AI-written.
"""

import re
from textwrap import dedent

# ------------------------------------------------------------------
# AI writing signals (heuristic)
# ------------------------------------------------------------------

# Phrases heavily overused by LLMs — multi-word or clearly resume-specific
# NOTE: no single punctuation characters, no common English words
AI_PHRASES = [
    "leverage",
    "leveraging",
    "leveraged",
    "spearheaded",
    "orchestrated",
    "championed",
    "utilized",
    "utilizing",
    "streamlined",
    "synergy",
    "synergies",
    "paradigm",
    "robust",
    "scalable",
    "cutting-edge",
    "innovative solution",
    "transformative",
    "dynamic professional",
    "result-driven",
    "results-driven",
    "detail-oriented",
    "passionate about",
    "proven track record",
    "cross-functional",
    "value-added",
    "best-in-class",
    "thought leader",
    "deep dive",
    "move the needle",
    "circle back",
    "at the end of the day",
    "in order to",
    "it is worth noting",
    "it should be noted",
    "moreover",
    "furthermore",
    "in conclusion",
    "to summarize",
    "as an ai",
    "as a language model",
    "i cannot",
    "i'm unable",
]

# Passive voice indicators
PASSIVE_PATTERNS = [
    r"\bwas\s+\w+ed\b",
    r"\bwere\s+\w+ed\b",
    r"\bbeen\s+\w+ed\b",
    r"\bis\s+\w+ed\b",
    r"\bare\s+\w+ed\b",
]

# Overly long sentence threshold (words)
LONG_SENTENCE_THRESHOLD = 35


def heuristic_score(text: str) -> dict:
    """
    Fast heuristic AI detection.

    Returns:
        {
            "score": int (0-100),
            "ai_phrases_found": list[str],
            "passive_voice_count": int,
            "long_sentence_count": int,
            "avg_sentence_length": float,
            "signals": list[str]   # human-readable findings
        }
    """
    if not text or not text.strip():
        return {
            "score": 0,
            "ai_phrases_found": [],
            "passive_voice_count": 0,
            "long_sentence_count": 0,
            "avg_sentence_length": 0.0,
            "signals": [],
        }

    lower = text.lower()
    signals = []
    penalty = 0

    # 1. AI phrase detection — use word-boundary matching to avoid
    #    false positives from hyphens, bullet dashes, or substrings
    def _phrase_match(phrase: str, text: str) -> bool:
        if " " in phrase or "-" in phrase:
            return phrase in text  # multi-word / hyphenated: substring ok
        return bool(re.search(r"\b" + re.escape(phrase) + r"\b", text))

    found_phrases = [p for p in AI_PHRASES if _phrase_match(p, lower)]
    phrase_score = min(len(found_phrases) * 6, 40)
    penalty += phrase_score
    if found_phrases:
        signals.append(
            f"{len(found_phrases)} AI-associated phrase(s) detected: "
            f"{', '.join(found_phrases[:5])}"
            + (" and more..." if len(found_phrases) > 5 else "")
        )

    # 2. Passive voice
    passive_count = sum(len(re.findall(pat, lower)) for pat in PASSIVE_PATTERNS)
    passive_score = min(passive_count * 4, 20)
    penalty += passive_score
    if passive_count:
        signals.append(f"{passive_count} passive voice construction(s) found.")

    # 3. Long sentences
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    long_sentences = [s for s in sentences if len(s.split()) > LONG_SENTENCE_THRESHOLD]
    long_score = min(len(long_sentences) * 5, 20)
    penalty += long_score
    if long_sentences:
        signals.append(
            f"{len(long_sentences)} overly long sentence(s) detected "
            f"(>{LONG_SENTENCE_THRESHOLD} words)."
        )

    # 4. Sentence length uniformity (AI tends to write very uniform sentences)
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 15 and len(sentences) > 4:
            penalty += 10
            signals.append(
                "Sentence length is unusually uniform — a common AI pattern."
            )
    else:
        avg = 0.0
        variance = 0.0

    # 5. Repetitive sentence starters — skip bullets/punctuation tokens
    _word_re = re.compile(r"[a-zA-Z]{2,}")
    starter_words = []
    for s in sentences:
        tokens = s.split()
        # Find the first real word (skip leading dashes, bullets, symbols)
        for tok in tokens:
            if _word_re.fullmatch(tok.strip(".,;:!?'\"-")):
                starter_words.append(tok.lower().strip(".,;:!?'\"-"))
                break
    if starter_words:
        most_common = max(set(starter_words), key=starter_words.count)
        ratio = starter_words.count(most_common) / len(starter_words)
        if ratio > 0.3:
            penalty += 8
            signals.append(
                f"Repetitive sentence starters detected "
                f"('{most_common}' used {starter_words.count(most_common)} times)."
            )

    score = min(int(penalty), 100)

    if not signals:
        signals.append("No strong AI writing signals detected.")

    return {
        "score": score,
        "ai_phrases_found": found_phrases,
        "passive_voice_count": passive_count,
        "long_sentence_count": len(long_sentences),
        "avg_sentence_length": round(avg, 1) if sentences else 0.0,
        "signals": signals,
    }


def deep_analysis(text: str) -> dict:
    """
    OpenAI-powered deep AI detection.

    Returns:
        {
            "score": int (0-100),
            "verdict": str,
            "reasoning": str,
            "suggestions": list[str]
        }
    """
    from services.openai_client import OpenAIClient

    client = OpenAIClient()

    prompt = dedent(
        f"""
        You are an expert at detecting AI-generated text in professional resumes.

        Analyze the following resume text and estimate the likelihood it was
        written (fully or partially) by an AI language model.

        Return your response in this EXACT format (no extra text):

        SCORE: <integer 0-100>
        VERDICT: <one of: "Likely Human", "Possibly AI-Assisted", "Likely AI-Generated">
        REASONING: <2-3 sentences explaining your assessment>
        SUGGESTIONS:
        - <specific suggestion to make it sound more human>
        - <specific suggestion to make it sound more human>
        - <specific suggestion to make it sound more human>

        RESUME:
        {text[:3000]}
    """
    )

    try:
        raw = client.generate(prompt, temperature=0.2, max_tokens=400)
        return _parse_deep_response(raw)
    except Exception as e:
        print(f"[AI DETECTOR] Deep analysis failed: {e}")
        return {
            "score": -1,
            "verdict": "Analysis failed",
            "reasoning": str(e),
            "suggestions": [],
        }


def _parse_deep_response(raw: str) -> dict:
    result = {
        "score": -1,
        "verdict": "Unknown",
        "reasoning": "",
        "suggestions": [],
    }

    lines = raw.strip().splitlines()
    in_suggestions = False

    for line in lines:
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                result["score"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("VERDICT:"):
            result["verdict"] = line.replace("VERDICT:", "").strip()
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.replace("REASONING:", "").strip()
        elif line.startswith("SUGGESTIONS:"):
            in_suggestions = True
        elif in_suggestions and line.startswith("-"):
            result["suggestions"].append(line.lstrip("- ").strip())

    return result
