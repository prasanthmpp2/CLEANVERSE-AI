"""
VisionAgent — Simulates AI image analysis for uploaded complaint photos.

In a production system, this would call Google Vision API or a custom
YOLO model. For hackathon DEMO mode, it uses deterministic simulation
based on file metadata and pseudo-random seeding to produce realistic output.
"""

import hashlib
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional


# ─── Detection Labels ─────────────────────────────────────────────────────────
GARBAGE_TYPES = [
    "Plastic Bottles", "Food Waste", "Construction Debris", "Medical Waste",
    "Paper & Cardboard", "Metal Scrap", "Organic Compost Pile", "Black-bag Refuse",
    "Textile Waste", "E-Waste", "Mixed Municipal Solid Waste",
]

RISK_FACTORS = [
    "Open drainage nearby — risk of waterborne disease",
    "Adjacent to residential area — resident health hazard",
    "High vehicle traffic point — accident risk",
    "Near water body — aquatic ecosystem threat",
    "Children's play zone — immediate health alert",
    "Commercial zone — public image deterioration",
    "Proximity to food stalls — food security concern",
]

VISUAL_CONDITIONS = [
    "Daylight — Clear visibility, good image quality",
    "Overcast — Moderate visibility",
    "Low-light evening — Partial visibility",
    "Night-time — Low visibility, torch illumination",
    "Rainy conditions — Degraded image quality",
]


@dataclass
class VisionResult:
    image_analyzed: bool
    image_filename: Optional[str]
    file_size_kb: float
    garbage_detected: bool
    garbage_probability: float        # 0.0–1.0
    detected_objects: List[str]
    estimated_volume_m3: float
    risk_factors: List[str]
    visual_condition: str
    hazardous_materials: bool
    cleanliness_score: int            # 0–100 (lower = dirtier)
    vision_confidence: float          # 0.0–1.0
    notes: str


class VisionAgent:
    """
    Analyzes uploaded images for garbage/cleanliness detection.
    Uses simulation seeded with the image hash for deterministic demo results.
    """

    name = "VisionAgent"
    version = "1.0.0"

    def run(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        analyzer_severity: int = 5,
    ) -> VisionResult:

        # ── No image provided ─────────────────────────────────────────────────
        if image_path is None and image_bytes is None:
            return VisionResult(
                image_analyzed=False,
                image_filename=None,
                file_size_kb=0.0,
                garbage_detected=False,
                garbage_probability=0.0,
                detected_objects=[],
                estimated_volume_m3=0.0,
                risk_factors=[],
                visual_condition="No image provided",
                hazardous_materials=False,
                cleanliness_score=70,
                vision_confidence=0.0,
                notes="No image was submitted with this complaint. Text analysis only.",
            )

        # ── Compute seed from image data or path ──────────────────────────────
        if image_bytes:
            seed_val = int(hashlib.md5(image_bytes[:512]).hexdigest(), 16) % (2 ** 31)
            file_size_kb = len(image_bytes) / 1024
        else:
            seed_val = int(hashlib.md5(image_path.encode()).hexdigest(), 16) % (2 ** 31)
            file_size_kb = os.path.getsize(image_path) / 1024 if os.path.exists(image_path) else 50.0

        rng = random.Random(seed_val + analyzer_severity)

        # ── Simulate detection ────────────────────────────────────────────────
        # Higher analyzer severity = more likely to detect garbage
        base_prob = 0.55 + (analyzer_severity - 5) * 0.04
        garbage_probability = max(0.1, min(0.97, base_prob + rng.uniform(-0.1, 0.1)))
        garbage_detected = garbage_probability > 0.45

        num_objects = rng.randint(2, 5)
        detected_objects = rng.sample(GARBAGE_TYPES, min(num_objects, len(GARBAGE_TYPES)))

        num_risks = rng.randint(1, 3)
        detected_risks = rng.sample(RISK_FACTORS, min(num_risks, len(RISK_FACTORS)))

        visual_condition = rng.choice(VISUAL_CONDITIONS)
        hazardous = rng.random() > 0.65 and analyzer_severity >= 7

        # Volume: 0.1 – 4.8 cubic metres
        volume = round(rng.uniform(0.1, 4.8), 2)

        # Cleanliness score inversely proportional to probability
        cleanliness = max(5, min(95, int((1 - garbage_probability) * 100)))

        confidence = round(rng.uniform(0.78, 0.97), 2)

        ext = os.path.splitext(filename or "image.jpg")[1].upper() or "JPEG"
        notes = (
            f"[DEMO] Vision model (YOLOv8-Nano simulation) processed {ext} image "
            f"({file_size_kb:.1f} KB). "
            f"Garbage probability: {garbage_probability:.0%}. "
            f"{'⚠️ Hazardous materials flagged.' if hazardous else 'No hazardous materials detected.'}"
        )

        return VisionResult(
            image_analyzed=True,
            image_filename=filename,
            file_size_kb=round(file_size_kb, 1),
            garbage_detected=garbage_detected,
            garbage_probability=round(garbage_probability, 2),
            detected_objects=detected_objects,
            estimated_volume_m3=volume,
            risk_factors=detected_risks,
            visual_condition=visual_condition,
            hazardous_materials=hazardous,
            cleanliness_score=cleanliness,
            vision_confidence=confidence,
            notes=notes,
        )
