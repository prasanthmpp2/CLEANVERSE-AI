"""
CLEANVERSE AI — Autonomous Smart City Intelligence Platform
FastAPI Backend — main.py

Run with:
    pip install -r requirements.txt
    uvicorn main:app --reload
"""

import os
import uuid
import shutil
import traceback
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ─── Internal modules ─────────────────────────────────────────────────────────
from firebase.firebase_config import (
    add_document, get_collection, get_document,
    update_document, is_demo_mode
)
from agents.analyzer_agent import AnalyzerAgent
from agents.vision_agent import VisionAgent
from agents.decision_agent import DecisionAgent
from agents.prediction_agent import PredictionAgent
from agents.demo_seeder import seed_demo_data

# ─── App Initialization ───────────────────────────────────────────────────────
app = FastAPI(
    title="CLEANVERSE AI",
    description="Autonomous Smart City Intelligence Platform for Urban Cleanliness",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── Agent Singletons ─────────────────────────────────────────────────────────
analyzer_agent   = AnalyzerAgent()
vision_agent     = VisionAgent()
decision_agent   = DecisionAgent()
prediction_agent = PredictionAgent()


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("  CLEANVERSE AI -- Smart City Intelligence Platform")
    print("  Version: 2.0.0 | Mode:", "DEMO" if is_demo_mode() else "LIVE Firebase")
    print("=" * 60)
    seed_demo_data()
    print("[OK] Server ready. Open http://127.0.0.1:8000 in your browser.\n")


# ─── Login Page ───────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse, tags=["Frontend"])
async def login_page(request: Request):
    """Serve the Firebase Authentication login page."""
    return templates.TemplateResponse("login.html", {"request": request})


# ─── Root / Dashboard ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def root(request: Request):
    """Serve the main CLEANVERSE AI Command Center dashboard."""
    demo_mode = is_demo_mode()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "demo_mode": demo_mode}
    )


# ─── POST /complaint ──────────────────────────────────────────────────────────
@app.post("/complaint", tags=["Complaints"])
async def submit_complaint(
    text: str = Form(..., description="Complaint description text"),
    location: str = Form(..., description="Location of the issue"),
    image: Optional[UploadFile] = File(None, description="Optional image upload"),
):
    """
    Submit a new citizen complaint.

    Triggers the full AI Agent Pipeline:
    1. AnalyzerAgent — NLU classification
    2. VisionAgent   — Image analysis
    3. DecisionAgent — Priority + action plan
    """
    complaint_id = str(uuid.uuid4())
    image_url    = None
    image_bytes  = None
    filename     = None

    # ── Save uploaded image ───────────────────────────────────────────────────
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        filename = f"{complaint_id}{ext}"
        save_path = os.path.join(UPLOAD_DIR, filename)

        image_bytes = await image.read()
        with open(save_path, "wb") as f:
            f.write(image_bytes)

        image_url = f"/static/uploads/{filename}"

    # ── Run AI Agent Pipeline ─────────────────────────────────────────────────
    try:
        # Agent 1: Analyze text
        ar = analyzer_agent.run(text, location)

        # Agent 2: Analyze image
        vr = vision_agent.run(
            image_bytes=image_bytes,
            filename=filename,
            analyzer_severity=ar.severity_score,
        )

        # Agent 3: Decision + action plan
        dr = decision_agent.run(ar, vr)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent pipeline failed: {str(e)}")

    # ── Build and store document ──────────────────────────────────────────────
    document = {
        "id": complaint_id,
        "text": text,
        "location": location,
        "imageUrl": image_url,
        "status": "analyzing",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "isDemo": False,
        "aiAnalysis": {
            "category": ar.category,
            "categoryEmoji": ar.category_emoji,
            "issueType": ar.issue_type,
            "keywords": ar.keywords_found,
            "sentiment": ar.sentiment,
            "severityScore": ar.severity_score,
            "urgencyBoost": ar.urgency_boost,
            "summary": ar.summary,
            "analyzerConfidence": round(ar.confidence, 2),
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

    add_document("complaints", document)

    return {
        "success": True,
        "complaintId": complaint_id,
        "message": "Complaint received and analysed by CLEANVERSE AI agents.",
        "aiAnalysis": document["aiAnalysis"],
    }


# ─── GET /complaints ──────────────────────────────────────────────────────────
@app.get("/complaints", tags=["Complaints"])
async def list_complaints(limit: int = 50):
    """Retrieve all complaints ordered by most recent."""
    complaints = get_collection("complaints", limit=limit)
    return {"count": len(complaints), "complaints": complaints}


# ─── GET /complaint/{id} ──────────────────────────────────────────────────────
@app.get("/complaint/{complaint_id}", tags=["Complaints"])
async def get_complaint(complaint_id: str):
    """Retrieve a single complaint by ID."""
    doc = get_document("complaints", complaint_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return doc


# ─── GET /dashboard ───────────────────────────────────────────────────────────
@app.get("/dashboard", tags=["Dashboard"])
async def get_dashboard_data():
    """
    Returns aggregated stats for the command center dashboard.
    """
    complaints = get_collection("complaints", limit=200)

    total = len(complaints)
    status_counts = {"pending": 0, "analyzing": 0, "dispatched": 0, "resolved": 0}
    urgency_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    category_counts: dict = {}
    priority_scores: list = []
    cleanliness_scores: list = []

    for c in complaints:
        ai = c.get("aiAnalysis", {})
        dec = ai.get("decision", {})
        vis = ai.get("visionResult", {})

        # Status
        s = c.get("status", "pending")
        status_counts[s] = status_counts.get(s, 0) + 1

        # Urgency
        uk = dec.get("urgencyKey", "low")
        urgency_counts[uk] = urgency_counts.get(uk, 0) + 1

        # Category
        cat = ai.get("category", "Unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Scores
        ps = dec.get("priorityScore", 0)
        if ps:
            priority_scores.append(ps)

        cs = vis.get("cleanlinessScore", 0)
        if cs:
            cleanliness_scores.append(cs)

    avg_priority = round(sum(priority_scores) / len(priority_scores), 1) if priority_scores else 0
    avg_cleanliness = round(sum(cleanliness_scores) / len(cleanliness_scores), 1) if cleanliness_scores else 75

    # Top 5 by priority
    top_complaints = sorted(
        [c for c in complaints if c.get("aiAnalysis", {}).get("decision", {}).get("priorityScore")],
        key=lambda x: x["aiAnalysis"]["decision"]["priorityScore"],
        reverse=True,
    )[:5]

    return {
        "totalComplaints": total,
        "statusCounts": status_counts,
        "urgencyCounts": urgency_counts,
        "categoryDistribution": category_counts,
        "averagePriorityScore": avg_priority,
        "cityCleanlinessIndex": avg_cleanliness,
        "topPriorityComplaints": top_complaints,
        "demoMode": is_demo_mode(),
    }


# ─── GET /prediction ──────────────────────────────────────────────────────────
@app.get("/prediction", tags=["Prediction"])
async def run_prediction():
    """
    Run the PredictionAgent on all stored complaints and return hotspot forecasts.
    """
    complaints = get_collection("complaints", limit=200)
    result = prediction_agent.run(complaints)

    return {
        "generatedAt": result.generated_at,
        "totalAnalyzed": result.total_complaints_analyzed,
        "cityCleanlinessIndex": result.city_cleanliness_index,
        "forecastSummary": result.forecast_summary,
        "modelVersion": result.model_version,
        "hotspots": [
            {
                "rank": h.rank,
                "zone": h.zone,
                "lat": h.lat,
                "lng": h.lng,
                "riskScore": h.risk_score,
                "complaintCount": h.complaint_count,
                "trendLabel": h.trend_label,
                "trendDescription": h.trend_description,
                "predicted24h": h.predicted_incidents_24h,
                "predicted7d": h.predicted_incidents_7d,
                "recommendedAction": h.recommended_action,
            }
            for h in result.hotspots
        ],
    }


# ─── GET /status ──────────────────────────────────────────────────────────────
@app.get("/status", tags=["System"])
async def system_status():
    """System health check."""
    return {
        "status": "online",
        "platform": "CLEANVERSE AI v2.0",
        "firebaseMode": "demo" if is_demo_mode() else "live",
        "agents": {
            "analyzer": AnalyzerAgent.name,
            "vision": VisionAgent.name,
            "decision": DecisionAgent.name,
            "prediction": PredictionAgent.name,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
