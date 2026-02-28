"""
AnalyzerAgent — Understands and classifies raw citizen complaint text.

This agent performs Natural Language Understanding (NLU) on the complaint
and produces a structured category, keywords, and a severity estimate
without requiring an external API (rule-based with realistic simulation).
"""

import re
import random
from dataclasses import dataclass, field
from typing import List, Optional


# ─── Issue Category Taxonomy ──────────────────────────────────────────────────
ISSUE_MAP = {
    "garbage": {
        "keywords": ["garbage", "trash", "waste", "litter", "dump", "rubbish", "debris",
                     "refuse", "filth", "sewage", "drain", "stink", "smell", "odor"],
        "category": "Solid Waste Management",
        "emoji": "🗑️",
        "base_severity": 6,
    },
    "pothole": {
        "keywords": ["pothole", "road", "crater", "broken", "uneven", "damaged road",
                     "pavement", "asphalt", "stuck", "tyre", "tire"],
        "category": "Road Infrastructure",
        "emoji": "🚧",
        "base_severity": 5,
    },
    "water": {
        "keywords": ["flood", "waterlog", "overflow", "leak", "pipe", "sewage", "drainage",
                     "stagnant", "puddle", "inundation"],
        "category": "Water & Drainage",
        "emoji": "💧",
        "base_severity": 7,
    },
    "air": {
        "keywords": ["smoke", "pollution", "air", "toxic", "fumes", "dust", "smog",
                     "burning", "fire", "haze"],
        "category": "Air Quality",
        "emoji": "💨",
        "base_severity": 6,
    },
    "noise": {
        "keywords": ["noise", "loud", "sound", "horn", "construction", "vibration", "disturbance"],
        "category": "Noise Pollution",
        "emoji": "🔊",
        "base_severity": 4,
    },
    "encroachment": {
        "keywords": ["encroach", "illegal", "slum", "unauthorized", "occupied", "blockage",
                     "obstruct", "hawker", "vendor"],
        "category": "Encroachment & Illegal Occupation",
        "emoji": "🚫",
        "base_severity": 5,
    },
    "lighting": {
        "keywords": ["dark", "light", "street light", "lamp", "broken light", "no power",
                     "electricity", "blackout"],
        "category": "Street Lighting",
        "emoji": "💡",
        "base_severity": 4,
    },
    "animal": {
        "keywords": ["dog", "cow", "animal", "stray", "pest", "rat", "mosquito",
                     "insect", "reptile", "bird"],
        "category": "Animal & Pest Control",
        "emoji": "🐾",
        "base_severity": 5,
    },
}

URGENCY_WORDS = ["urgent", "emergency", "critical", "immediately", "asap", "danger",
                 "hazard", "accident", "injury", "children", "hospital", "school"]

VOLUME_WORDS = {
    "massive": 9, "huge": 8, "large": 7, "big": 6, "medium": 5,
    "small": 3, "tiny": 2, "little": 2,
}


@dataclass
class AnalyzerResult:
    category: str
    category_emoji: str
    issue_type: str
    keywords_found: List[str]
    sentiment: str
    severity_score: int          # 1-10
    urgency_boost: bool
    summary: str
    confidence: float            # 0.0 – 1.0
    raw_text: str
    token_count: int


class AnalyzerAgent:
    """
    Classifies a citizen complaint into a structured issue category.
    Uses deterministic rule-based matching for hackathon demo reliability.
    """

    name = "AnalyzerAgent"
    version = "1.0.0"

    def run(self, complaint_text: str, location: Optional[str] = None) -> AnalyzerResult:
        text_lower = complaint_text.lower()

        # 1. Category detection
        best_match = None
        best_count = 0

        for key, meta in ISSUE_MAP.items():
            found = [kw for kw in meta["keywords"] if kw in text_lower]
            if len(found) > best_count:
                best_count = len(found)
                best_match = (key, meta, found)

        if best_match is None:
            # Default fallback
            best_match = (
                "garbage",
                ISSUE_MAP["garbage"],
                [],
            )
            confidence = 0.4
        else:
            confidence = min(0.99, 0.5 + best_count * 0.12)

        issue_type, meta, keywords_found = best_match

        # 2. Severity calculation
        severity = meta["base_severity"]

        urgency_boost = any(uw in text_lower for uw in URGENCY_WORDS)
        if urgency_boost:
            severity = min(10, severity + 2)

        for vol_word, bump in VOLUME_WORDS.items():
            if vol_word in text_lower:
                severity = min(10, max(severity, bump))
                break

        # 3. Sentiment
        negative_words = ["worst", "horrible", "terrible", "disgusting", "filthy",
                          "awful", "unbearable", "pathetic", "negligent"]
        if any(w in text_lower for w in negative_words):
            sentiment = "Highly Negative"
        elif urgency_boost:
            sentiment = "Urgent / Distressed"
        else:
            sentiment = "Negative"

        # 4. Summary generation
        location_str = f" at {location}" if location else ""
        summary = (
            f"Citizen reported a '{meta['category']}' issue{location_str}. "
            f"Detected keywords: {', '.join(keywords_found) if keywords_found else 'general concern'}. "
            f"Estimated severity: {severity}/10."
        )

        token_count = len(complaint_text.split())

        return AnalyzerResult(
            category=meta["category"],
            category_emoji=meta["emoji"],
            issue_type=issue_type,
            keywords_found=keywords_found,
            sentiment=sentiment,
            severity_score=severity,
            urgency_boost=urgency_boost,
            summary=summary,
            confidence=confidence,
            raw_text=complaint_text,
            token_count=token_count,
        )
