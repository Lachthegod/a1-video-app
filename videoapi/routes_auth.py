# videoapi/routes_auth.py
from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import RedirectResponse
from videoapi.cognito import (
    sign_up_user, confirm_user, authenticate_user, respond_to_mfa_challenge
)
import requests
import os
import jwt
from jose import jwk, jwt as jose_jwt, JWTError
from jose.utils import base64url_decode
import time
import secrets

router = APIRouter()

COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "ttsd47doobrmjbrv7fbkoe4smvviop002996m1g6h47drlqq7cu")
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN", "https://ap-southeast-2kuurldbyk.auth.ap-southeast-2.amazoncognito.com")


# Load Cognito JWKS once
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


@router.post("/signup")
async def signup(username: str = Body(...), password: str = Body(...), email: str = Body(...)):
    try:
        result = sign_up_user(username, password, email)
        return {"message": "User signed up", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm")
async def confirm(username: str = Body(...), code: str = Body(...)):
    try:
        result = confirm_user(username, code)
        return {"message": "User confirmed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    try:
        return authenticate_user(username, password)

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



@router.post("/mfa")
async def mfa(username: str = Body(...), session: str = Body(...), code: str = Body(...), challenge: str = Body(...)):
    """
    Handle MFA challenge. Returns Cognito tokens after successful MFA.
    """
    try:
        return respond_to_mfa_challenge(username, session, code, challenge)
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


