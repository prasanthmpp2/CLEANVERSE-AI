"""
Demo Data Generator — Seeds realistic complaints into the store for instant demo.
Call seed_demo_data() once on startup when no complaints exist.
"""

import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from firebase.firebase_config import add_document, get_collection
from agents.analyzer_agent import AnalyzerAgent
from agents.vision_agent import VisionAgent
from agents.decision_agent import DecisionAgent

DEMO_COMPLAINTS = [
    {
        "text": "Large pile of construction debris blocking the footpath near Meenakshi Temple entrance. Very dangerous for pilgrims.",
        "location": "Meenakshi Temple Area",
        "hours_ago": 2,
    },
    {
        "text": "Overflowing garbage bin outside Periyar Bus Stand. Extremely foul smell. Children are playing nearby!",
        "location": "Periyar Bus Stand",
        "hours_ago": 5,
    },
    {
        "text": "Stagnant water flooding the road near Mattuthavani Market junction. Cars are stuck. Urgent action needed!",
        "location": "Mattuthavani Market",
        "hours_ago": 8,
    },
    {
        "text": "Huge pile of mixed waste dumped illegally along the K.K. Nagar main road. Medical waste bags visible.",
        "location": "K.K. Nagar Residential",
        "hours_ago": 12,
    },
    {
        "text": "Pothole at Tallakulam Junction is getting bigger after rain. Several bike accidents reported.",
        "location": "Tallakulam Junction",
        "hours_ago": 18,
    },
    {
        "text": "Street lights not working on Anna Nagar Main Road. Very dark and unsafe at night.",
        "location": "Anna Nagar Main Road",
        "hours_ago": 24,
    },
    {
        "text": "Stray cattle blocking traffic near Goripalayam overbridge. Garbage scattered around them.",
        "location": "Goripalayam Overbridge",
        "hours_ago": 30,
    },
    {
        "text": "Burning of plastic waste near Azhagar Kovil Road. Thick black smoke visible from 1 km away.",
        "location": "Azhagar Kovil Road",
        "hours_ago": 36,
    },
    {
        "text": "Illegal encroachment on footpath at Bye-pass road stretch. Hawkers blocking emergency vehicle access.",
        "location": "Bypass Road Stretch",
        "hours_ago": 48,
    },
    {
        "text": "Broken drainage near Simmakkal Circle causing sewage overflow. Very unhygienic condition.",
        "location": "Simmakkal Circle",
        "hours_ago": 72,
    },
]

STATUSES = ["resolved", "dispatched", "dispatched", "pending", "analyzing"]


def seed_demo_data() -> int:
    """Seeds demo complaints if fewer than 5 complaints exist. Returns count added."""
    existing = get_collection("complaints", limit=5)
    if len(existing) >= 5:
        return 0

    analyzer = AnalyzerAgent()
    vision   = VisionAgent()
    decision = DecisionAgent()
    now      = datetime.now(timezone.utc)

    added = 0
    for item in DEMO_COMPLAINTS:
        complaint_id = str(uuid.uuid4())
        created_at   = (now - timedelta(hours=item["hours_ago"])).isoformat()

        # Run agents
        ar = analyzer.run(item["text"], item["location"])
        vr = vision.run()                                  # no image
        dr = decision.run(ar, vr)

        rng    = random.Random(hash(item["text"]) & 0xFFFFFF)
        status = rng.choice(STATUSES)

        doc = {
            "id": complaint_id,
            "text": item["text"],
            "location": item["location"],
            "imageUrl": None,
            "status": status,
            "createdAt": created_at,
            "isDemo": True,
            "aiAnalysis": {
                "category": ar.category,
                "categoryEmoji": ar.category_emoji,
                "issueType": ar.issue_type,
                "keywords": ar.keywords_found,
                "sentiment": ar.sentiment,
                "severityScore": ar.severity_score,
                "urgencyBoost": ar.urgency_boost,
                "summary": ar.summary,
                "analyzerConfidence": ar.confidence,
                "visionResult": {
                    "imageAnalyzed": vr.image_analyzed,
                    "garbageDetected": vr.garbage_detected,
                    "garbageProbability": vr.garbage_probability,
                    "detectedObjects": vr.detected_objects,
                    "estimatedVolume": vr.estimated_volume_m3,
                    "riskFactors": vr.risk_factors,
                    "hazardous": vr.hazardous_materials,
                    "cleanlinessScore": vr.cleanliness_score,
                    "notes": vr.notes,
                },
                "decision": {
                    "priorityScore": dr.priority_score,
                    "urgencyKey": dr.urgency_key,
                    "urgencyLabel": dr.urgency_label,
                    "urgencyColor": dr.urgency_color,
                    "responseHours": dr.response_hours,
                    "department": dr.department,
                    "xaiReasoning": dr.xai_reasoning,
                    "compositeInputs": dr.composite_inputs,
                    "actionPlan": {
                        "method": dr.action_plan.method,
                        "steps": dr.action_plan.action_steps,
                        "equipment": dr.action_plan.equipment,
                        "estimatedCostINR": dr.action_plan.estimated_cost_inr,
                        "estimatedResponseHours": dr.action_plan.estimated_response_hours,
                    },
                },
            },
        }

        add_document("complaints", doc)
        added += 1

    print(f"[OK] Seeded {added} demo complaints.")
    return added
