# videoapi/routes_auth.py
from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import RedirectResponse
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
sessions = {}


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
        tokens = authenticate_user(username, password)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/mfa")
async def mfa(username: str = Body(...), session: str = Body(...), code: str = Body(...), challenge: str = Body(...)):
    try:
        tokens = respond_to_mfa_challenge(username, session, code, challenge)
        return tokens
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
        "client_secret": COGNITO_CLIENT_SECRET
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

    # Step 2: Verify ID token signature
    try:
        unverified_headers = jwt.get_unverified_header(id_token)
        kid = unverified_headers["kid"]
        key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key_data:
            raise HTTPException(status_code=401, detail="Invalid token key")

        public_key = jwk.construct(key_data)
        message, encoded_sig = id_token.rsplit('.', 1)
        decoded_sig = base64url_decode(encoded_sig.encode())
        if not public_key.verify(message.encode(), decoded_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")

        payload = jwt.decode(id_token, options={"verify_signature": False})
        # You can also validate 'aud', 'iss', 'exp' here manually if you want
    except JWTError as e:
        return {"error": f"Invalid token: {str(e)}"}

    # Step 3: Generate your app session token
    user_sub = payload.get("sub")
    username = payload.get("cognito:username") or payload.get("email")

    session_token = secrets.token_urlsafe(32)  # random session ID
    sessions[session_token] = {
        "sub": user_sub,
        "username": username,
        "expires_at": time.time() + 3600  # 1 hour session
    }

    # Step 4: Redirect user to dashboard with session token
    dashboard_url = f"http://vidy.cab432.com:8080/dashboard/{session_token}"
    return RedirectResponse(dashboard_url)