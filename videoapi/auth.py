from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "DeezNutz"  # Will need to change for future assessments
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hard coded admin and user accounts, shows in web client too
users = {
    "admin": {"id": 1, "password": "admin", "role": "admin"},
    "user1": {"id": 2, "password": "password1", "role": "user"},
}

security = HTTPBearer()

def generate_access_token(username: str):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    payload = {
        "sub": username,
        "id": user["id"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def authenticate_user(username: str, password: str):
    user = users.get(username)
    if user and user["password"] == password:
        return user
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")

        if username is None or username not in users:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return {"username": username, "id": user_id, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
