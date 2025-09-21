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
REDIRECT_URI = "https://vidy.cab432.com:3000/callback"

# Load Cognito JWKS once
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()

# In-memory session store (replace with Redis or DB in production)
#sessions = {}


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

# @router.post("/login")
# async def login(username: str = Body(...), password: str = Body(...)):
#     try:
#         tokens = authenticate_user(username, password)
#         return tokens
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=str(e))


@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    try:
        return authenticate_user(username, password)

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



# @router.post("/mfa")
# async def mfa(username: str = Body(...), session: str = Body(...), code: str = Body(...), challenge: str = Body(...)):
#     try:
#         tokens = respond_to_mfa_challenge(username, session, code, challenge)
#         return tokens
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=str(e))

@router.post("/mfa")
async def mfa(username: str = Body(...), session: str = Body(...), code: str = Body(...), challenge: str = Body(...)):
    """
    Handle MFA challenge. Returns Cognito tokens after successful MFA.
    """
    try:
        return respond_to_mfa_challenge(username, session, code, challenge)
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



@router.get("/callback")
async def cognito_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code in callback"}

    # Step 1: Exchange code for tokens
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": COGNITO_CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_secret": COGNITO_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        tokens = response.json()
    except Exception as e:
        return {"error": f"Failed to get tokens: {str(e)}"}

    id_token = tokens.get("id_token")
    if not id_token:
        return {"error": "Failed to get ID token"}

    # Step 2: Verify and decode ID token
    try:
        claims = jose_jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}",
        )
    except JWTError as e:
        return {"error": f"Invalid token: {str(e)}"}

    # Step 3: Redirect back to frontend with tokens (or set cookies)
    # Option A: pass tokens in query string (less secure)
    # dashboard_url = f"http://vidy.cab432.com:8080/dashboard?id_token={tokens['id_token']}&access_token={tokens['access_token']}"

    # Option B: set tokens in secure, HttpOnly cookies (better for web apps)
    response = RedirectResponse(url="http://vidy.cab432.com:8080/dashboard")
    response.set_cookie("id_token", tokens["id_token"], httponly=True, secure=True, max_age=tokens["expires_in"])
    response.set_cookie("access_token", tokens["access_token"], httponly=True, secure=True, max_age=tokens["expires_in"])
    if "refresh_token" in tokens:
        response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True, secure=True)

    return response
