import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from firebase_admin import firestore

from models.schemas import GoogleAuthRequest, AuthResponse

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_change_this")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ALGORITHM = "HS256"


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")


@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest):
    """Autentificare cu Google ID Token primit de pe mobil."""
    try:
        info = id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token Google invalid: {e}")

    user_id = info["sub"]
    email = info.get("email", "")
    name = info.get("name", "")
    picture = info.get("picture")

    # Salvare / actualizare utilizator în Firestore
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        "email": email,
        "name": name,
        "picture": picture,
        "last_login": datetime.now(timezone.utc).isoformat(),
    }, merge=True)

    access_token = create_access_token(user_id, email)

    return AuthResponse(
        access_token=access_token,
        user_id=user_id,
        email=email,
        name=name,
        picture=picture,
    )
