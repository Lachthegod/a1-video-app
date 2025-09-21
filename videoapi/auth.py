
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
import requests
import os

# -----------------------------
# Cognito Config
# -----------------------------
COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}"

jwks = requests.get(JWKS_URL).json()
security = HTTPBearer()


def verify_token(token: str):
    try:
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )
        return claims
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")

    claims = verify_token(credentials.credentials)

    username = claims.get("cognito:username") or claims.get("username")
    groups = claims.get("cognito:groups", [])
    sub = claims.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    return {
        "username": username,
        "id": sub,
        "role": groups[0] if groups else "user",
    }
