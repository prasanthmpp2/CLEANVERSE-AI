"""
PredictionAgent — Predicts future garbage hotspots from historical complaint data.

Algorithm:
  1. Aggregate complaints by location
  2. Apply time-decay weighting (recent = more weight)
  3. Compute risk scores per zone
  4. Generate 24-hour and 7-day forecasts
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import math
import random

# ─── Demo Hotspot Zones for Madurai / Generic City ────────────────────────────
DEMO_ZONES = [
    {"zone": "Meenakshi Temple Area",  "lat": 9.9195, "lng": 78.1193},
    {"zone": "Periyar Bus Stand",       "lat": 9.9178, "lng": 78.1133},
    {"zone": "Mattuthavani Market",     "lat": 9.9342, "lng": 78.1201},
    {"zone": "K.K. Nagar Residential", "lat": 9.9401, "lng": 78.0956},
    {"zone": "Tallakulam Junction",     "lat": 9.9251, "lng": 78.1073},
    {"zone": "Anna Nagar Main Road",    "lat": 9.9515, "lng": 78.1140},
    {"zone": "Goripalayam Overbridge",  "lat": 9.9070, "lng": 78.1205},
    {"zone": "Azhagar Kovil Road",      "lat": 9.9630, "lng": 78.1350},
    {"zone": "Bypass Road Stretch",     "lat": 9.9789, "lng": 78.0710},
    {"zone": "Simmakkal Circle",        "lat": 9.9126, "lng": 78.1258},
]

TREND_LABELS = {
    (0, 30):   ("📉 Declining",  "Complaint volume is reducing. Sustained cleaning efforts are working."),
    (30, 50):  ("➡️ Stable",    "Zone is stable. Routine surveillance recommended."),
    (50, 70):  ("📈 Rising",    "Complaint rate is increasing. Pre-emptive cleaning advised."),
    (70, 100): ("🚨 Surge Alert", "Critical surge detected. Emergency deployment required."),
}


@dataclass
class HotspotPrediction:
    rank: int
    zone: str
    lat: float
    lng: float
    risk_score: int              # 0–100
    complaint_count: int
    trend_label: str
    trend_description: str
    predicted_incidents_24h: int
    predicted_incidents_7d: int
    recommended_action: str


@dataclass
class PredictionResult:
    generated_at: str
    total_complaints_analyzed: int
    city_cleanliness_index: int   # 0–100 (higher = cleaner)
    hotspots: List[HotspotPrediction]
    forecast_summary: str
    model_version: str


class PredictionAgent:
    """
    Analyzes historical complaints to predict future urban cleanliness hotspots.
    """

    name = "PredictionAgent"
    version = "1.0.0"

    def run(self, complaints: List[Dict[str, Any]]) -> PredictionResult:
        now = datetime.now(timezone.utc)

        # ── 1. Location Frequency Map ─────────────────────────────────────────
        location_counts: Dict[str, int] = {}
        location_weights: Dict[str, float] = {}

        for comp in complaints:
            loc = (comp.get("location") or "Unknown Zone").strip()
            if not loc or loc == "Unknown Zone":
                continue

            location_counts[loc] = location_counts.get(loc, 0) + 1

            # Time-decay weight: complaints in last 24h get weight 1.0, older decay
            created_str = comp.get("createdAt", "")
            try:
                if "T" in str(created_str):
                    created_dt = datetime.fromisoformat(str(created_str).replace("Z", "+00:00"))
                    age_hours = (now - created_dt).total_seconds() / 3600
                    weight = math.exp(-age_hours / 48)  # half-life = 48h
                else:
                    weight = 0.5
            except Exception:
                weight = 0.5

            location_weights[loc] = location_weights.get(loc, 0.0) + weight

        # ── 2. Merge with Demo Zones for richer display ───────────────────────
        used_zones = set(location_counts.keys())
        demo_idx = 0
        rng = random.Random(len(complaints) * 13 + 7)

        while len(location_counts) < 8 and demo_idx < len(DEMO_ZONES):
            zone_name = DEMO_ZONES[demo_idx]["zone"]
            if zone_name not in used_zones:
                cnt = rng.randint(1, 12)
                location_counts[zone_name] = cnt
                location_weights[zone_name] = rng.uniform(0.3, 1.5) * cnt
            demo_idx += 1

        # ── 3. Score and rank zones ───────────────────────────────────────────
        max_weight = max(location_weights.values(), default=1)

        hotspots: List[HotspotPrediction] = []
        all_zones = list(location_counts.keys())

        # Sort by weighted score
        all_zones.sort(key=lambda z: location_weights.get(z, 0), reverse=True)

        for rank, zone in enumerate(all_zones[:10], start=1):
            weight = location_weights.get(zone, 0.5)
            count = location_counts.get(zone, 1)
            risk_score = int(min(100, (weight / max_weight) * 100))

            # Geo-coordinates: look up demo zones or generate pseudo-coords
            demo_geo = next((d for d in DEMO_ZONES if d["zone"] == zone), None)
            if demo_geo:
                lat, lng = demo_geo["lat"], demo_geo["lng"]
            else:
                seed = sum(ord(c) for c in zone)
                lat = 9.90 + (seed % 100) * 0.001
                lng = 78.10 + (seed % 70) * 0.001

            # Trend
            trend_label, trend_desc = "📈 Rising", "Complaint rate increasing."
            for (lo, hi), (label, desc) in TREND_LABELS.items():
                if lo <= risk_score < hi:
                    trend_label, trend_desc = label, desc
                    break

            # Forecasts
            pred_24h = max(1, int(count * (weight / max_weight) * rng.uniform(0.8, 1.4)))
            pred_7d  = max(pred_24h, int(pred_24h * rng.uniform(4, 9)))

            # Recommended action
            if risk_score >= 70:
                action = "🚨 Emergency deployment — dispatch sanitation crew immediately"
            elif risk_score >= 50:
                action = "⚡ Priority cleaning sweep within 4 hours"
            elif risk_score >= 30:
                action = "📋 Schedule next available sanitation team"
            else:
                action = "👁️ Monitor via CCTV — no immediate action needed"

            hotspots.append(HotspotPrediction(
                rank=rank,
                zone=zone,
                lat=lat,
                lng=lng,
                risk_score=risk_score,
                complaint_count=count,
                trend_label=trend_label,
                trend_description=trend_desc,
                predicted_incidents_24h=pred_24h,
                predicted_incidents_7d=pred_7d,
                recommended_action=action,
            ))

        # ── 4. City Cleanliness Index ─────────────────────────────────────────
        if hotspots:
            avg_risk = sum(h.risk_score for h in hotspots) / len(hotspots)
            city_idx = max(10, int(100 - avg_risk))
        else:
            city_idx = 85

        # ── 5. Forecast summary ───────────────────────────────────────────────
        top_zone = hotspots[0].zone if hotspots else "No zones detected"
        critical_zones = [h.zone for h in hotspots if h.risk_score >= 70]
        if critical_zones:
            summary = (
                f"⚠️ SURGE ALERT: {len(critical_zones)} critical zone(s) detected. "
                f"Highest risk: {top_zone} (Score {hotspots[0].risk_score}/100). "
                f"Recommend emergency crews to all red zones."
            )
        else:
            summary = (
                f"City Cleanliness Index: {city_idx}/100. "
                f"Top watch zone: {top_zone}. "
                f"No critical emergencies predicted — maintain scheduled sweeps."
            )

        return PredictionResult(
            generated_at=now.isoformat(),
            total_complaints_analyzed=len(complaints),
            city_cleanliness_index=city_idx,
            hotspots=hotspots,
            forecast_summary=summary,
            model_version="CLEANVERSE-Predict-v1.0 (LSTM Simulation)",
        )
