from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
import requests
from parameter_store import load_parameters


# -----------------------------
# Cognito Config
# -----------------------------

security = HTTPBearer()
parameters = load_parameters()

AWS_REGION = "ap-southeast-2"
COGNITO_USER_POOL_ID = parameters.get("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = parameters.get("COGNITO_CLIENT_ID")

JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

jwks = requests.get(JWKS_URL).json()


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
