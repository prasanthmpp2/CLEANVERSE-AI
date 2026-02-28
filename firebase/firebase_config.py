"""
Firebase configuration and initialization module.
Supports both real Firebase (via service account) and demo mode (in-memory store).
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ─── DEMO MODE STORAGE ────────────────────────────────────────────────────────
# Used when Firebase credentials are not available. Data lives in memory.
_DEMO_STORE: Dict[str, List[Dict]] = {
    "complaints": [],
    "decisions": [],
    "predictions": [],
}

_firebase_initialized = False
_firestore_client = None


def _try_init_firebase():
    """Attempt to initialize Firebase Admin SDK. Falls back to demo mode."""
    global _firebase_initialized, _firestore_client

    if _firebase_initialized:
        return

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
            else:
                # Try inline JSON from environment variable
                sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if sa_json:
                    sa_dict = json.loads(sa_json)
                    cred = credentials.Certificate(sa_dict)
                else:
                    raise FileNotFoundError("No Firebase credentials found.")

            firebase_admin.initialize_app(cred)

        _firestore_client = firestore.client()
        _firebase_initialized = True
        print("[OK] Firebase Firestore connected successfully.")

    except Exception as e:
        print(f"[WARN] Firebase not available ({e}). Running in DEMO mode with in-memory store.")
        _firebase_initialized = False
        _firestore_client = None


_try_init_firebase()


# ─── FIRESTORE WRAPPER ────────────────────────────────────────────────────────

def add_document(collection: str, data: Dict[str, Any]) -> str:
    """Add a document to a Firestore collection (or demo store)."""
    doc_id = data.get("id", str(uuid.uuid4()))
    data["id"] = doc_id
    data.setdefault("createdAt", datetime.now(timezone.utc).isoformat())

    if _firestore_client:
        try:
            from firebase_admin import firestore as fs
            data_to_store = {k: v for k, v in data.items()}
            data_to_store["createdAt"] = fs.SERVER_TIMESTAMP
            ref = _firestore_client.collection(collection).document(doc_id)
            ref.set(data_to_store)
            return doc_id
        except Exception as e:
            print(f"Firestore write error: {e}. Falling back to demo store.")

    # Demo mode fallback
    _DEMO_STORE.setdefault(collection, [])
    # Remove duplicates by id before appending
    _DEMO_STORE[collection] = [d for d in _DEMO_STORE[collection] if d.get("id") != doc_id]
    _DEMO_STORE[collection].append(data)
    return doc_id


def get_collection(collection: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve documents from a Firestore collection (or demo store)."""
    if _firestore_client:
        try:
            docs = (
                _firestore_client.collection(collection)
                .order_by("createdAt", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            results = []
            for doc in docs:
                d = doc.to_dict()
                d["id"] = doc.id
                # Convert Firestore timestamps to ISO strings
                if hasattr(d.get("createdAt"), "isoformat"):
                    d["createdAt"] = d["createdAt"].isoformat()
                results.append(d)
            return results
        except Exception as e:
            print(f"Firestore read error: {e}. Falling back to demo store.")

    return list(reversed(_DEMO_STORE.get(collection, [])))[:limit]


def get_document(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single document by ID."""
    if _firestore_client:
        try:
            ref = _firestore_client.collection(collection).document(doc_id)
            doc = ref.get()
            if doc.exists:
                d = doc.to_dict()
                d["id"] = doc.id
                return d
            return None
        except Exception as e:
            print(f"Firestore read error: {e}.")

    for doc in _DEMO_STORE.get(collection, []):
        if doc.get("id") == doc_id:
            return doc
    return None


def update_document(collection: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """Update fields on an existing document."""
    if _firestore_client:
        try:
            ref = _firestore_client.collection(collection).document(doc_id)
            ref.update(updates)
            return True
        except Exception as e:
            print(f"Firestore update error: {e}.")

    for doc in _DEMO_STORE.get(collection, []):
        if doc.get("id") == doc_id:
            doc.update(updates)
            return True
    return False


def is_demo_mode() -> bool:
    return not _firebase_initialized


def get_demo_store() -> Dict[str, List[Dict]]:
    return _DEMO_STORE
