import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()

# Inițializare Firebase — citește din variabilă de mediu (cloud) sau fișier (local)
firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
if firebase_credentials_json:
    cred = credentials.Certificate(json.loads(firebase_credentials_json))
else:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json"))

firebase_admin.initialize_app(cred)

from routers import auth, workouts, sessions

app = FastAPI(
    title="RunCoach API",
    description="Backend pentru aplicația de antrenament RunCoach",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(workouts.router, prefix="/workouts", tags=["Workouts"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])

@app.get("/")
def root():
    return {"status": "RunCoach API is running 🏃"}