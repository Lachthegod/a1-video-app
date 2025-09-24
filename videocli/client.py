

######################################
from fastapi import FastAPI, Form, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.templating import Jinja2Templates
import uuid
import httpx
from jose import jwt, jwk, JWTError
import os
import logging
import boto3
from botocore.exceptions import ClientError
import json


def get_secret(secret_name="n11715910-cognito", region_name="ap-southeast-2"):

    client = boto3.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Error retrieving secret {secret_name}: {e}")

    secret_str = get_secret_value_response.get('SecretString')
    logging.info(f"client secret str", secret_str)

    return secret_str
    



COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN", "https://ap-southeast-2kuurldbyk.auth.ap-southeast-2.amazoncognito.com")
COGNITO_CLIENT_SECRET = get_secret()

# -----------------------------
# Cognito Config
# -----------------------------
COGNITO_REGION = "ap-southeast-2"
COGNITO_USERPOOL_ID = "ap-southeast-2_KUuRLDBYK"
COGNITO_CLIENT_ID = "1nc5drgnphkq8i4d2rusnfoa36"
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"

REDIRECT_URI = os.getenv("COGNITO_REDIRECT_URI", "https://0uzcd4dvda.execute-api.ap-southeast-2.amazonaws.com/v1/callback")

GOOGLE_LOGIN_URL = (
    f"{COGNITO_DOMAIN}/login"
    f"?response_type=code"
    f"&client_id={COGNITO_CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&identity_provider=Google"
)


# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
logging.basicConfig(level=logging.INFO)



templates = Jinja2Templates(directory="templates")
API_BASE = "http://video-api:3000"
SESSIONS = {}  # in-memory session store

# -----------------------------
# Async JWKS fetch
# -----------------------------
_jwks_cache = None
async def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            _jwks_cache = resp.json()
    return _jwks_cache

# -----------------------------
# JWT decode
# -----------------------------

async def decode_jwt(id_token: str, access_token: str = None):
    try:
        jwks = await get_jwks()
        unverified_headers = jwt.get_unverified_header(id_token)
        kid = unverified_headers["kid"]
        logging.info(f"JWT header kid={kid}")

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            logging.warning("No matching JWK found for kid")
            return None, None

        public_key = jwk.construct(key)

        payload = None

        try:
            payload = jwt.decode(
                id_token,
                public_key.to_pem().decode(),
                algorithms=["RS256"],
                audience=COGNITO_CLIENT_ID,
                access_token=access_token,  
            )
            logging.info("JWT successfully decoded with audience check (likely IdToken)")
        except JWTError as e:
            logging.warning(f"JWT audience decode failed → {e}")
            try:
                payload = jwt.decode(
                    id_token,
                    public_key.to_pem().decode(),
                    algorithms=["RS256"],
                    options={"verify_aud": False},  
                )
                logging.info("JWT successfully decoded without audience (likely AccessToken)")
            except JWTError as e2:
                logging.warning(f"JWT decode failed in both modes → {e2}")
                return None, None

        username = payload.get("cognito:username") or payload.get("username")
        role = payload.get("cognito:groups", ["user"])[0]
        token_use = payload.get("token_use", "unknown")

        logging.info(f"Decoded JWT → token_use={token_use}, username={username}, role={role}")
        logging.info(f"Full decoded JWT payload: {payload}")

        return username, role

    except Exception as e:
        logging.error(f"Unexpected error in decode_jwt: {e}", exc_info=True)
        return None, None




# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "google_login_url": GOOGLE_LOGIN_URL})



@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
        if resp.status_code != 200:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
        data = resp.json()

        if "challenge" in data:
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = {
                "username": username,
                "session": data["session"],
                "challenge": data["challenge"],
            }
            return RedirectResponse(f"/mfa/{session_id}", status_code=303)

        token = data["IdToken"]
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = token
        return RedirectResponse(f"/dashboard/{session_id}", status_code=303)
    

# -----------------------------
# Dashboard
# -----------------------------

@app.get("/dashboard/{session_id}", response_class=HTMLResponse)
async def dashboard(request: Request, session_id: str):
    logging.info(f"=== /dashboard endpoint hit for session_id={session_id} ===")

    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    # Determine tokens
    if isinstance(session, str):
        # Manual login
        id_token = session
        access_token = session
    elif isinstance(session, dict):
        # Google login
        id_token = session.get("IdToken")
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    

    
    if not id_token or not access_token:
        logging.warning(f"Missing IdToken or AccessToken for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    logging.info("Decoding JWT to extract username and role...")

    username, role = await decode_jwt(id_token, access_token)
    if not username:
        logging.warning(f"Failed to decode JWT for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    logging.info(f"Decoded JWT → username={username}, role={role}")

    headers = {"Authorization": f"Bearer {access_token}"}
    videos, tasks = [], []

    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    sort_by = request.query_params.get("sort_by", "created_at")
    order = request.query_params.get("order", "desc")
    status = request.query_params.get("status")
    owner_filter = request.query_params.get("owner")
    search = request.query_params.get("search")

    logging.info(
        f"Query params → skip={skip}, limit={limit}, sort_by={sort_by}, "
        f"order={order}, status={status}, owner={owner_filter}, search={search}"
    )

    try:
        timeout = httpx.Timeout(60.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            params = {
                "skip": skip,
                "limit": limit,
                "sort_by": sort_by,
                "order": order,
                "status": status,
                "owner": owner_filter,
                "search": search,
            }
            logging.info(f"Requesting videos from API → {API_BASE}/videos/ with params={params}")
            resp = await client.get(f"{API_BASE}/videos/", headers=headers, params=params)
            logging.info(f"API /videos/ response status={resp.status_code}")

            resp_json = resp.json()
            all_videos = resp_json.get("items", [])
            logging.info(f"Fetched {len(all_videos)} total videos from API")

            if role == "admin":
                logging.info("User is admin → fetching tasks as well")
                videos = all_videos
                resp_tasks = await client.get(f"{API_BASE}/videos/tasks", headers=headers)
                logging.info(f"API /videos/tasks response status={resp_tasks.status_code}")
                if resp_tasks.status_code == 200:
                    tasks = resp_tasks.json()
                    logging.info(f"Fetched {len(tasks)} tasks")
            else:
                videos = [v for v in all_videos if v["owner"] == username]
                logging.info(f"User is normal user → filtered down to {len(videos)} videos")

    except Exception as e:
        logging.error(f"Error fetching videos for session_id={session_id}: {e}", exc_info=True)

    template_name = "dashboard_admin.html" if role == "admin" else "dashboard_user.html"
    logging.info(f"Rendering template={template_name} for username={username}")

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "videos": videos,
            "session_id": session_id,
            "username": username,
            "role": role,
            "tasks": tasks,
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "order": order,
            "status": status,
            "owner_filter": owner_filter,
            "search": search,
        },
    )

# -----------------------------
# Upload video
# -----------------------------

@app.post("/upload/{session_id}")
async def upload(session_id: str, filename: str = Form(...), content_type: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    if isinstance(session, str):
        access_token = session
    elif isinstance(session, dict):
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}

    # Request backend to generate presigned URL
    async with httpx.AsyncClient() as client:
        presign_resp = await client.post(
            f"{API_BASE}/videos/",
            headers=headers,
            json={"filename": filename, "content_type": content_type},
        )
        presign_resp.raise_for_status()
        presign_data = presign_resp.json()

    # Return JSON directly
    return JSONResponse(
        {
            "upload_url": presign_data["upload_url"],
            "object_key": presign_data["object_key"],
        }
    )


#will need to add the n11715910-a2.cab432.com domain in the CORS for security reasons


# -----------------------------
# Delete video
# -----------------------------
@app.post("/delete/{session_id}/{video_id}")
async def delete(session_id: str, video_id: int):

    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    if isinstance(session, str):
        access_token = session
    elif isinstance(session, dict):
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE}/videos/{video_id}", headers=headers)

    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


# -----------------------------
# Transcode video
# -----------------------------
@app.post("/transcode/{session_id}/{video_id}/{fmt}")
async def transcode(session_id: str, video_id: int, fmt: str):

    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    if isinstance(session, str):
        access_token = session
    elif isinstance(session, dict):
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}
    timeout = httpx.Timeout(300.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.post(
            f"{API_BASE}/videos/{video_id}/transcode",
            json={"format": fmt},
            headers=headers,
        )

    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


# -----------------------------
# Update metadata
# -----------------------------
@app.post("/update_metadata/{session_id}/{video_id}")
async def update_metadata(
    session_id: str,
    video_id: int,
    title: str = Form(None),
    description: str = Form(None),
):
    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    if isinstance(session, str):
        access_token = session
    elif isinstance(session, dict):
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    payload = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if not payload:
        return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}
    timeout = httpx.Timeout(60.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.put(f"{API_BASE}/videos/{video_id}", json=payload, headers=headers)

    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


# -----------------------------
# Logout
# -----------------------------
@app.get("/logout/{session_id}")
async def logout(session_id: str):
    SESSIONS.pop(session_id, None)
    return RedirectResponse("/", status_code=303)


# -----------------------------
# Signup
# -----------------------------
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/signup",
            json={"username": username, "password": password, "email": email}
        )

    if resp.status_code != 200:
        return templates.TemplateResponse("signup.html", {"request": request, "error": resp.text})
    return RedirectResponse("/confirm", status_code=303)


# -----------------------------
# Confirm account
# -----------------------------
@app.get("/confirm", response_class=HTMLResponse)
async def confirm_page(request: Request):
    return templates.TemplateResponse("confirm.html", {"request": request})

@app.post("/confirm")
async def confirm(request: Request, username: str = Form(...), code: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/confirm",
            json={"username": username, "code": code}
        )

    if resp.status_code != 200:
        return templates.TemplateResponse("confirm.html", {"request": request, "error": await resp.text()})
    return RedirectResponse("/", status_code=303)


# Example for download:
@app.get("/download/{session_id}/{video_id}")
async def download(session_id: str, video_id: int):
    session = SESSIONS.get(session_id)
    if not session:
        logging.warning(f"No session found for session_id={session_id}")
        return RedirectResponse("/", status_code=303)
    
    if isinstance(session, str):
        access_token = session
    elif isinstance(session, dict):
        access_token = session.get("AccessToken")
    else:
        logging.warning(f"Invalid session type for session_id={session_id}")
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/videos/{video_id}/download", headers=headers)
        if resp.status_code != 200:
            return RedirectResponse(f"/dashboard/{session_id}", status_code=303)
        data = resp.json()
        download_url = data.get("download_url")
        if not download_url:
            return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

        return RedirectResponse(download_url)

# --- MFA routes ---
@app.get("/mfa/{session_id}", response_class=HTMLResponse)
async def mfa_page(request: Request, session_id: str):
    return templates.TemplateResponse("mfa.html", {"request": request, "session_id": session_id})

@app.post("/mfa/{session_id}")
async def mfa_submit(request: Request, session_id: str, code: str = Form(...)):
    session_data = SESSIONS.get(session_id)
    if not session_data:
        return RedirectResponse("/", status_code=303)

    username = session_data["username"]
    session_token = session_data["session"]
    challenge = session_data["challenge"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/mfa",
            json={"username": username, "session": session_token, "code": code, "challenge": challenge},
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "mfa.html",
            {"request": request, "session_id": session_id, "error": "Invalid code"},
        )

    tokens = resp.json()
    token = tokens["IdToken"]
    SESSIONS[session_id] = token
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

# -----------------------------
# OAuth2 Callback for Google/Cognito
# -----------------------------

@app.get("/callback")
async def auth_callback(request: Request, code: str = None, state: str = None):
    logging.info("=== /callback endpoint hit ===")

    if not code:
        logging.error("Missing 'code' parameter in callback URL")
        raise HTTPException(status_code=400, detail="Missing code parameter")

    logging.info(f"Received code: {code}")
    logging.info(f"Received state: {state}")

    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": COGNITO_CLIENT_ID,
        "client_secret": get_secret(),
        "code": code,
        "redirect_uri": "https://0uzcd4dvda.execute-api.ap-southeast-2.amazonaws.com/v1/callback",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    logging.info(f"Exchanging code for tokens at {token_url}")
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data, headers=headers)
        logging.info(f"Token endpoint response status: {resp.status_code}")
        logging.debug(f"Token endpoint response body: {resp.text}")

        if resp.status_code != 200:
            logging.error(f"Failed to exchange code: {resp.text}")
            raise HTTPException(status_code=400, detail=f"Failed to exchange code: {resp.text}")

        tokens = resp.json()

    # Log what came back (don’t log secrets fully in prod — mask them!)
    logging.info("Successfully received tokens from Cognito")
    logging.debug(f"Raw tokens: {tokens}")
    logging.info(f"Raw tokens: {tokens}")

    session_id = str(uuid.uuid4())
    logging.info(f"Generated session_id: {session_id}")

    SESSIONS[session_id] = {
        "AccessToken": tokens.get("access_token"),
        "IdToken": tokens.get("id_token"),
        "RefreshToken": tokens.get("refresh_token"),
        "ExpiresIn": tokens.get("expires_in"),
        "TokenType": tokens.get("token_type"),
    }
    logging.info("Stored tokens in SESSIONS")

    redirect_url = f"http://n11715910-a2.cab432.com:3001/dashboard/{session_id}"
    logging.info(f"Redirecting user to {redirect_url}")

    return RedirectResponse(redirect_url, status_code=303)



