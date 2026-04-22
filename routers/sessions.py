from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import firestore
import uuid

from models.schemas import Session, SessionCreate, SessionComparison
from routers.workouts import get_current_user

router = APIRouter()


@router.post("/", response_model=Session)
async def save_session(
    body: SessionCreate,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    session_id = str(uuid.uuid4())

    session_data = {
        **body.dict(),
        "id": session_id,
        "user_id": user_id,
    }

    db.collection("sessions").document(session_id).set(session_data)
    return Session(**session_data)


@router.get("/history", response_model=list)
async def get_history(
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    docs = (
        db.collection("sessions")
        .where("user_id", "==", user_id)
        .order_by("started_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


@router.get("/compare/{workout_id}", response_model=SessionComparison)
async def compare_sessions(
    workout_id: str,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    docs = list(
        db.collection("sessions")
        .where("user_id", "==", user_id)
        .where("workout_id", "==", workout_id)
        .order_by("started_at", direction=firestore.Query.DESCENDING)
        .limit(2)
        .stream()
    )

    if not docs:
        raise HTTPException(status_code=404, detail="Nicio sesiune găsită pentru acest antrenament")

    current = Session(**docs[0].to_dict())
    previous = Session(**docs[1].to_dict()) if len(docs) > 1 else None

    improvement_seconds = None
    improvement_meters = None

    if previous:
        improvement_seconds = previous.duration_seconds - current.duration_seconds
        improvement_meters = current.distance_meters - previous.distance_meters

    return SessionComparison(
        current=current,
        previous=previous,
        improvement_seconds=improvement_seconds,
        improvement_meters=improvement_meters,
    )


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    doc = db.collection("sessions").document(session_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Sesiune negăsită")

    session = Session(**doc.to_dict())
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acces interzis")

    return session