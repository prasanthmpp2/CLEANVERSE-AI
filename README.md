# ⚡ CLEANVERSE AI — Autonomous Smart City Intelligence Platform

> *An AI-powered urban cleanliness operating system for Madurai City*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange?logo=firebase)](https://firebase.google.com)

---

## 🌐 What is CLEANVERSE AI?

CLEANVERSE AI is a **Multi-Agent Smart City Platform** where citizens report cleanliness issues and autonomous AI agents instantly **analyze, classify, prioritize, and predict** urban problems — forming a full city intelligence operating system.

---

## 🚀 Quick Start (2 minutes)

```bash
# 1. Navigate to project
cd cleanverse-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload

# 4. Open browser
http://127.0.0.1:8000
```

> **No Firebase credentials needed!** The system runs in full DEMO mode with 10 pre-seeded realistic Madurai city incidents.

---

## 🗂️ Project Structure

```
cleanverse-ai/
├── main.py                      ← FastAPI application (all API routes)
├── requirements.txt             ← Python dependencies
├── README.md                    ← This file
│
├── agents/                      ← AI Agent System
│   ├── __init__.py
│   ├── analyzer_agent.py        ← NLU text classification
│   ├── vision_agent.py          ← Image garbage detection (simulation)
│   ├── decision_agent.py        ← Priority scoring + action plans
│   ├── prediction_agent.py      ← Hotspot forecasting
│   └── demo_seeder.py           ← Auto-seeds demo data on startup
│
├── firebase/                    ← Firebase integration
│   ├── __init__.py
│   └── firebase_config.py       ← Admin SDK init + CRUD wrapper
│
├── templates/
│   └── index.html               ← Main HTML dashboard (Jinja2)
│
└── static/
    ├── css/
    │   └── dashboard.css        ← Full dark cyberpunk styling
    ├── js/
    │   └── dashboard.js         ← Frontend controller
    └── uploads/                 ← Uploaded images (auto-created)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Command Center Dashboard (HTML) |
| `POST` | `/complaint` | Submit complaint + trigger AI pipeline |
| `GET`  | `/complaints` | List all complaints |
| `GET`  | `/complaint/{id}` | Single complaint details |
| `GET`  | `/dashboard` | Aggregated KPI stats |
| `GET`  | `/prediction` | Run hotspot prediction model |
| `GET`  | `/status` | System health check |

Interactive API docs: **http://127.0.0.1:8000/docs**

---

## 🧠 AI Agent Pipeline

When a complaint is submitted, four agents execute sequentially:

```
Citizen Input (text + image)
        │
        ▼
 ┌─────────────────┐
 │  AnalyzerAgent  │ — NLU: Classifies issue type, extracts keywords,
 │                 │         measures severity (1-10)
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │   VisionAgent   │ — Image: Detects garbage, estimates volume,
 │                 │         flags hazardous materials
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  DecisionAgent  │ — Fusion: Computes Priority Score (1-100),
 │                 │         generates action plan + XAI reasoning
 └────────┬────────┘
          │
          ▼
 ┌──────────────────┐
 │ PredictionAgent  │ — Forecasts 24h/7d hotspots using time-decay
 │                  │   weighting across all historical complaints
 └──────────────────┘
```

---

## 🔥 Firebase Setup (Optional — for Live Mode)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a project → Enable **Firestore Database**
3. Go to **Project Settings → Service Accounts → Generate new private key**
4. Save the downloaded JSON as `serviceAccountKey.json` in the project root
5. Restart the server — it auto-detects and switches to **LIVE mode**

Firebase config (already integrated):
```
Project ID:  built-with-ai-e59a1
Auth Domain: built-with-ai-e59a1.firebaseapp.com
Storage:     built-with-ai-e59a1.firebasestorage.app
```

---

## 🎤 Hackathon Demo Script

1. **Open** `http://127.0.0.1:8000` — the Command Center loads with 10 pre-seeded incidents
2. **Click** `📡 Report Incident` → use a Quick Fill button or type your own
3. **Submit** → watch the AI Pipeline run in the Agent Log (bottom right)
4. **Switch** to `🗂️ Intelligence Feed` → see your complaint with full AI analysis
5. **Click** any card → view Priority Score, XAI Reasoning, Action Plan, Equipment
6. **Switch** to `🔮 Prediction Engine` → see hotspot risk map for Madurai
7. **Point out**: Real-time predictions, Explainable AI, Cost estimates, Department routing

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIREBASE_SERVICE_ACCOUNT` | Path to service account JSON | `serviceAccountKey.json` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Inline JSON string for cloud deployment | — |

---

## 📦 Dependencies

```
fastapi==0.110.0          ← Web framework
uvicorn[standard]==0.29.0 ← ASGI server
firebase-admin==6.5.0     ← Firestore integration
pydantic==2.6.4           ← Data validation
python-multipart==0.0.9   ← File upload support
aiofiles==23.2.1          ← Async file I/O
jinja2==3.1.3             ← HTML templating
httpx==0.27.0             ← Async HTTP client
```

---

## 🗺️ Feature Roadmap

- **V2**: Live Google Vision API + Gemini 1.5 Flash integration
- **V3**: Real-time drone feed + camera grid integration  
- **V4**: Citizen karma rewards via smart contracts
- **V5**: Autonomous vehicle dispatch via City Fleet API

---

*Built for Hackathon Demo | CLEANVERSE AI v2.0 | Madurai Smart City Initiative*
