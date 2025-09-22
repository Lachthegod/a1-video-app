

######################################

from fastapi import FastAPI, Form, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.templating import Jinja2Templates
import uuid
import httpx
from jose import jwt, jwk, JWTError
import aiofiles

# -----------------------------
# Cognito Config
# -----------------------------
COGNITO_REGION = "ap-southeast-2"
COGNITO_USERPOOL_ID = "ap-southeast-2_KUuRLDBYK"
COGNITO_CLIENT_ID = "1nc5drgnphkq8i4d2rusnfoa36"
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
API_BASE = "http://video-api:3000"


# -----------------------------
# Async JWKS fetch
# -----------------------------
async def get_jwks():
    async with httpx.AsyncClient() as client:
        resp = await client.get(JWKS_URL)
        return resp.json()

# -----------------------------
# JWT decode
# -----------------------------


async def decode_jwt(token: str):
    try:
        jwks = await get_jwks()
        unverified_headers = jwt.get_unverified_header(token)
        kid = unverified_headers["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            return None, None

        public_key = jwk.construct(key)
        payload = jwt.decode(
            token,
            public_key.to_pem().decode(),
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
        )
        username = payload.get("cognito:username") or payload.get("username")
        role = payload.get("cognito:groups", ["user"])[0]
        return username, role
    except JWTError:
        return None, None

# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -----------------------------
# Handle login form
# -----------------------------


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
        )

    if resp.status_code != 200:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    data = resp.json()

    if "challenge" in data:
        return templates.TemplateResponse(
            "mfa.html",
            {
                "request": request,
                "username": username,
                "password": password, 
                "session": data["session"],
                "challenge": data["challenge"],
            },
        )

    # Otherwise, set token cookie and redirect
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        key="id_token",
        value=data["IdToken"],
        httponly=True,
        secure=False,
        samesite="Strict",
        max_age=data.get("ExpiresIn", 3600),
    )
    return response


# -----------------------------
# Dashboard
# -----------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    token = request.cookies.get("id_token")
    if not token:
        return RedirectResponse("/", status_code=303)

    username, role = await decode_jwt(token)
    if not username:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    videos, tasks = [], []

    skip = int(request.query_params.get("skip", 0))
    limit = int(request.query_params.get("limit", 10))
    sort_by = request.query_params.get("sort_by", "created_at")
    order = request.query_params.get("order", "desc")
    status = request.query_params.get("status")
    owner_filter = request.query_params.get("owner")
    search = request.query_params.get("search")

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
            resp = await client.get(f"{API_BASE}/videos/", headers=headers, params=params)
            resp_json = resp.json()
            all_videos = resp_json.get("items", [])

            if role == "admin":
                videos = all_videos
                resp_tasks = await client.get(f"{API_BASE}/videos/tasks", headers=headers)
                if resp_tasks.status_code == 200:
                    tasks = resp_tasks.json()
            else:
                videos = [v for v in all_videos if v["owner"] == username]

    except Exception as e:
        print("Error fetching videos:", e)

    template_name = "dashboard_admin.html" if role == "admin" else "dashboard_user.html"
    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "videos": videos,
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

@app.post("/upload")
async def upload(request: Request, filename: str = Form(...), content_type: str = Form(...)):
    token = request.cookies.get("id_token")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid session")

    headers = {"Authorization": f"Bearer {token}"}

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
@app.post("/delete/{video_id}")
async def delete(request: Request, video_id: int):
    token = request.cookies.get("id_token")
    if not token:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE}/videos/{video_id}", headers=headers)

    return RedirectResponse(f"/dashboard", status_code=303)


# -----------------------------
# Transcode video
# -----------------------------
@app.post("/transcode/{video_id}/{fmt}")
async def transcode(request: Request, video_id: int, fmt: str):
    token = request.cookies.get("id_token")
    if not token:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(300.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.post(
            f"{API_BASE}/videos/{video_id}/transcode",
            json={"format": fmt},
            headers=headers,
        )

    return RedirectResponse(f"/dashboard", status_code=303)


# -----------------------------
# Update metadata
# -----------------------------
@app.post("/update_metadata/{video_id}")
async def update_metadata(
    request: Request,
    video_id: int,
    title: str = Form(None),
    description: str = Form(None),
):
    token = request.cookies.get("id_token")
    if not token:
        return RedirectResponse("/", status_code=303)

    payload = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if not payload:
        return RedirectResponse(f"/dashboard", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(60.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.put(f"{API_BASE}/videos/{video_id}", json=payload, headers=headers)

    return RedirectResponse(f"/dashboard", status_code=303)


# -----------------------------
# Logout
# -----------------------------

@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("id_token")
    return response


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
        return templates.TemplateResponse("confirm.html", {"request": request, "error": resp.text()})
    return RedirectResponse("/", status_code=303)


# Example for download:
@app.get("/download/{video_id}")
async def download(request: Request, video_id: int):
    token = request.cookies.get("id_token")
    if not token:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/videos/{video_id}/download", headers=headers)
        if resp.status_code != 200:
            return RedirectResponse(f"/dashboard", status_code=303)
        data = resp.json()
        download_url = data.get("download_url")
        if not download_url:
            return RedirectResponse(f"/dashboard", status_code=303)

        return RedirectResponse(download_url)

# --- MFA routes ---
@app.get("/mfa", response_class=HTMLResponse)
async def mfa_page(request: Request):
    return templates.TemplateResponse("mfa.html", {"request": request})


# -----------------------------
# MFA submit
# -----------------------------
@app.post("/mfa")
async def mfa_submit(
    request: Request,
    username: str = Form(...),
    session: str = Form(...),
    challenge: str = Form(...),
    code: str = Form(...),
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/mfa",
            json={"username": username, "session": session, "challenge": challenge, "code": code},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="MFA failed")

    data = resp.json()

    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        key="id_token",
        value=data["IdToken"],
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=data.get("ExpiresIn", 3600),
    )
    return response




