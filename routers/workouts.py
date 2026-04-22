from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_admin import firestore
import uuid

from models.schemas import Workout, WorkoutCreate
from routers.auth import verify_token

router = APIRouter()


def get_current_user(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Format token invalid")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    return payload["sub"]


@router.post("/", response_model=Workout)
async def create_workout(
    body: WorkoutCreate,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    workout_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    workout_data = {
        **body.dict(),
        "id": workout_id,
        "user_id": user_id,
        "created_at": now,
    }

    db.collection("workouts").document(workout_id).set(workout_data)
    return Workout(**workout_data)


@router.get("/", response_model=list)
async def list_workouts(user_id: str = Depends(get_current_user)):
    db = firestore.client()
    docs = (
        db.collection("workouts")
        .where("user_id", "==", user_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


@router.get("/{workout_id}", response_model=Workout)
async def get_workout(
    workout_id: str,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    doc = db.collection("workouts").document(workout_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Antrenament negăsit")

    workout = Workout(**doc.to_dict())
    if workout.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acces interzis")

    return workout


@router.put("/{workout_id}", response_model=Workout)
async def update_workout(
    workout_id: str,
    body: WorkoutCreate,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    ref = db.collection("workouts").document(workout_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Antrenament negăsit")

    existing = Workout(**doc.to_dict())
    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acces interzis")

    updated = {**existing.dict(), **body.dict()}
    ref.set(updated)
    return Workout(**updated)


@router.delete("/{workout_id}")
async def delete_workout(
    workout_id: str,
    user_id: str = Depends(get_current_user)
):
    db = firestore.client()
    ref = db.collection("workouts").document(workout_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Antrenament negăsit")

    if Workout(**doc.to_dict()).user_id != user_id:
        raise HTTPException(status_code=403, detail="Acces interzis")

    ref.delete()
    return {"detail": "Antrenament șters"}