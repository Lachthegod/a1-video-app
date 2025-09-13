# from fastapi import HTTPException, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import jwt
# from datetime import datetime, timedelta, timezone

# SECRET_KEY = "DeezNutz"  # Will need to change for future assessments
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# # Hard coded admin and user accounts, shows in web client too
# users = {
#     "admin": {"id": 1, "password": "admin", "role": "admin"},
#     "user": {"id": 2, "password": "user", "role": "user"},
# }

# security = HTTPBearer()

# def generate_access_token(username: str):
#     user = users.get(username)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid user")

#     payload = {
#         "sub": username,
#         "id": user["id"],
#         "role": user["role"],
#         "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     }
#     token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#     return token

# def authenticate_user(username: str, password: str):
#     user = users.get(username)
#     if user and user["password"] == password:
#         return user
#     return None

# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     if not credentials or credentials.scheme.lower() != "bearer":
#         raise HTTPException(status_code=401, detail="Unauthorized")
#     token = credentials.credentials
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         user_id = payload.get("id")
#         role = payload.get("role")

#         if username is None or username not in users:
#             raise HTTPException(status_code=401, detail="Unauthorized")

#         return {"username": username, "id": user_id, "role": role}
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import os

COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = credentials.credentials
    try:
        # Extract signing key
        unverified_headers = jwt.get_unverified_header(token)
        kid = unverified_headers["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token key")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

        # Verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID
        )

        username = payload.get("cognito:username") or payload.get("username")
        groups = payload.get("cognito:groups", [])
        sub = payload.get("sub")

        if not username:
            raise HTTPException(status_code=401, detail="Invalid token claims")

        return {
            "username": username,
            "id": sub,
            "role": groups[0] if groups else "user"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    