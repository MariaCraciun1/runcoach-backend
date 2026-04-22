from pydantic import BaseModel
from typing import List, Optional


# ── Auth ──────────────────────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    id_token: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None


# ── Workout ───────────────────────────────────────────────────────────────────

class Cue(BaseModel):
    id: str
    time_seconds: int
    message: str
    distance_meters: Optional[float] = None


class WorkoutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_seconds: int
    cues: List[Cue] = []


class Workout(WorkoutCreate):
    id: str
    user_id: str
    created_at: str


# ── Session ───────────────────────────────────────────────────────────────────

class LocationPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: float
    speed: Optional[float] = None


class SessionCreate(BaseModel):
    workout_id: str
    started_at: str
    ended_at: str
    duration_seconds: float
    distance_meters: float
    avg_speed_mps: float
    max_speed_mps: float
    route: List[LocationPoint] = []


class Session(SessionCreate):
    id: str
    user_id: str


class SessionComparison(BaseModel):
    current: Session
    previous: Optional[Session] = None
    improvement_seconds: Optional[float] = None
    improvement_meters: Optional[float] = None