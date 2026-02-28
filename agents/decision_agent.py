"""
DecisionAgent — Fuses Analyzer + Vision outputs into an actionable decision.

Responsibilities:
  - Assign final Priority Score (1-100)
  - Determine Urgency Level (Critical / High / Medium / Low)
  - Generate a Cleaning Action Plan with steps and equipment
  - Estimate cost and response time
"""

from dataclasses import dataclass, field
from typing import List, Optional
import random

from agents.analyzer_agent import AnalyzerResult
from agents.vision_agent import VisionResult


# ─── Action Plan Templates ────────────────────────────────────────────────────
ACTION_PLANS = {
    "Solid Waste Management": {
        "method": "Mechanised Sweeping + Compactor Collection",
        "steps": [
            "Deploy JCB / Tipper truck to site within 2 hours",
            "Segregate waste into dry, wet, and hazardous streams",
            "Load waste into compactor vehicle",
            "Transport to nearest Solid Waste Processing Facility",
            "Sanitize and disinfect the cleared area",
            "Install anti-dumping signage and CCTV warning",
            "Schedule weekly monitoring for repeat incidents",
        ],
        "equipment": ["Tipper Truck", "Compactor Van", "JCB Loader", "PPE Kits",
                      "Disinfectant Sprayer", "CCTV Camera Unit"],
        "cost_range": (2000, 15000),
    },
    "Road Infrastructure": {
        "method": "Pothole Patching + Bitumen Overlay",
        "steps": [
            "Place traffic diversion cones immediately",
            "Assess pothole depth and structural damage",
            "Remove loose debris and clean cavity",
            "Apply hot-mix bitumen patching compound",
            "Compact with road roller and cure for 4 hours",
            "Mark road surface and update road condition database",
        ],
        "equipment": ["Road Roller", "Bitumen Heater", "Cone Markers",
                      "Asphalt Patcher", "Survey Equipment"],
        "cost_range": (5000, 30000),
    },
    "Water & Drainage": {
        "method": "High-Pressure Suction + Desilting",
        "steps": [
            "Dispatch suction jetting machine to location",
            "Close nearby drainage inlets to prevent backflow",
            "Pump out stagnant water using submersible pumps",
            "Desilt clogged drains (depth: estimated 0.8–1.2m)",
            "Check and repair drainage pipe integrity",
            "Apply biocide to prevent mosquito breeding",
            "Test drainage flow post-clearance",
        ],
        "equipment": ["Suction Jetting Machine", "Submersible Pump",
                      "Desilting Excavator", "Biocide Sprayer"],
        "cost_range": (8000, 50000),
    },
    "Air Quality": {
        "method": "Source Identification + Emission Control",
        "steps": [
            "Deploy mobile air quality sensor to pinpoint source",
            "Issue stop-work order if industrial burning detected",
            "Coordinate with pollution control board",
            "Water sprinkle roads to suppress dust particles",
            "File FIR if open burning is willful",
        ],
        "equipment": ["Air Quality Sensor", "Water Sprinkler Truck", "Authority Notice Pads"],
        "cost_range": (1000, 20000),
    },
    "Noise Pollution": {
        "method": "Noise Level Assessment + Enforcement",
        "steps": [
            "Deploy decibel meter for baseline measurement",
            "Identify noise source — construction / industrial / traffic",
            "Issue formal noise complaint notice to violator",
            "Coordinate with traffic police for horn enforcement",
        ],
        "equipment": ["Decibel Meter", "Notice Forms", "Body Camera"],
        "cost_range": (500, 5000),
    },
    "Encroachment & Illegal Occupation": {
        "method": "Survey + Legal Action + Eviction",
        "steps": [
            "Document encroachment with GPS-tagged photographs",
            "Issue verbal and written notice to occupants",
            "Coordinate with Revenue Dept for survey records",
            "Engage district magistrate for eviction order",
            "Clear encroachment with supervised demolition team",
        ],
        "equipment": ["GPS Device", "Legal Notice Pads", "Demolition Tools"],
        "cost_range": (3000, 25000),
    },
    "Street Lighting": {
        "method": "Emergency Electrical Repair",
        "steps": [
            "Dispatch licensed electrician to site",
            "Check MCB / fuse in nearest street light panel",
            "Replace faulty bulb/LED unit if needed",
            "Test and restore supply, update asset log",
        ],
        "equipment": ["Ladder", "Multimeter", "Replacement LED Units", "Safety Gloves"],
        "cost_range": (500, 8000),
    },
    "Animal & Pest Control": {
        "method": "Humane Capture + Relocation / Treatment",
        "steps": [
            "Contact municipal animal control division",
            "Trap and vaccinate stray animals",
            "Relocate to nearby shelter or assigned zone",
            "Apply anti-pest treatment in affected area",
            "Educate community on feeding restrictions",
        ],
        "equipment": ["Animal Traps", "Vaccination Kits", "Pest Control Sprayer"],
        "cost_range": (1000, 10000),
    },
}

DEFAULT_PLAN = ACTION_PLANS["Solid Waste Management"]

URGENCY_LEVELS = {
    "critical": {"label": "🔴 CRITICAL", "response_hours": 1, "color": "#ff2d55"},
    "high":     {"label": "🟠 HIGH",     "response_hours": 4, "color": "#ff9f0a"},
    "medium":   {"label": "🟡 MEDIUM",   "response_hours": 24, "color": "#ffd60a"},
    "low":      {"label": "🟢 LOW",      "response_hours": 72, "color": "#30d158"},
}


@dataclass
class ActionPlan:
    method: str
    action_steps: List[str]
    equipment: List[str]
    estimated_cost_inr: int
    estimated_response_hours: int


@dataclass
class DecisionResult:
    priority_score: int              # 1–100
    urgency_key: str                 # critical / high / medium / low
    urgency_label: str
    urgency_color: str
    response_hours: int
    action_plan: ActionPlan
    department: str
    xai_reasoning: str               # Explainable AI narrative
    composite_inputs: dict           # Show judges what went into the score


class DecisionAgent:
    """
    Fuses analysis and vision results into a final decision with action plan.
    """

    name = "DecisionAgent"
    version = "1.0.0"

    DEPARTMENT_MAP = {
        "Solid Waste Management": "Solid Waste Management Department",
        "Road Infrastructure": "Public Works Department (PWD)",
        "Water & Drainage": "Water Resources & Drainage Board",
        "Air Quality": "Pollution Control Board",
        "Noise Pollution": "Environment & Noise Cell",
        "Encroachment & Illegal Occupation": "Revenue & Enforcement Wing",
        "Street Lighting": "Electrical Services Division",
        "Animal & Pest Control": "Animal Control & Pest Management Cell",
    }

    def run(
        self,
        analyzer: AnalyzerResult,
        vision: VisionResult,
    ) -> DecisionResult:

        # ── 1. Composite Priority Score Calculation ───────────────────────────
        # Weights:  Text severity 40% | Vision probability 35% | Hazard 15% | Volume 10%
        text_score   = analyzer.severity_score * 4.0          # max 40
        vision_score = vision.garbage_probability * 35.0      # max 35
        hazard_score = 15.0 if vision.hazardous_materials else 0.0
        volume_score = min(10.0, vision.estimated_volume_m3 * 2.0)  # max 10

        priority_score = int(min(100, text_score + vision_score + hazard_score + volume_score))

        # ── 2. Urgency Level ──────────────────────────────────────────────────
        if priority_score >= 75 or analyzer.urgency_boost or vision.hazardous_materials:
            urgency_key = "critical"
        elif priority_score >= 55:
            urgency_key = "high"
        elif priority_score >= 35:
            urgency_key = "medium"
        else:
            urgency_key = "low"

        urgency_meta = URGENCY_LEVELS[urgency_key]

        # ── 3. Action Plan ────────────────────────────────────────────────────
        plan_meta = ACTION_PLANS.get(analyzer.category, DEFAULT_PLAN)
        rng = random.Random(priority_score * 7 + len(analyzer.raw_text))
        cost = rng.randint(*plan_meta["cost_range"])

        action_plan = ActionPlan(
            method=plan_meta["method"],
            action_steps=plan_meta["steps"],
            equipment=plan_meta["equipment"],
            estimated_cost_inr=cost,
            estimated_response_hours=urgency_meta["response_hours"],
        )

        # ── 4. Department Routing ─────────────────────────────────────────────
        department = self.DEPARTMENT_MAP.get(analyzer.category, "Municipal Corporation")

        # ── 5. XAI Reasoning ─────────────────────────────────────────────────
        xai = (
            f"CLEANVERSE AI assigned a Priority Score of {priority_score}/100 based on: "
            f"Text Severity Index = {analyzer.severity_score}/10 (+{int(text_score)} pts), "
            f"Vision Garbage Probability = {vision.garbage_probability:.0%} (+{int(vision_score)} pts), "
            f"Hazardous Material Flag = {'YES' if vision.hazardous_materials else 'NO'} (+{int(hazard_score)} pts), "
            f"Estimated Volume = {vision.estimated_volume_m3} m³ (+{int(volume_score)} pts). "
            f"Urgency classified as '{urgency_key.upper()}' with mandatory response within "
            f"{urgency_meta['response_hours']} hour(s). "
            f"Routed to: {department}."
        )

        composite = {
            "text_severity_score": analyzer.severity_score,
            "text_contribution_pts": int(text_score),
            "vision_garbage_probability": vision.garbage_probability,
            "vision_contribution_pts": int(vision_score),
            "hazardous_flag": vision.hazardous_materials,
            "hazard_contribution_pts": int(hazard_score),
            "estimated_volume_m3": vision.estimated_volume_m3,
            "volume_contribution_pts": int(volume_score),
            "total_priority_score": priority_score,
        }

        return DecisionResult(
            priority_score=priority_score,
            urgency_key=urgency_key,
            urgency_label=urgency_meta["label"],
            urgency_color=urgency_meta["color"],
            response_hours=urgency_meta["response_hours"],
            action_plan=action_plan,
            department=department,
            xai_reasoning=xai,
            composite_inputs=composite,
        )
