from fastapi import FastAPI, Form, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io
import httpx
import uuid
import requests
from jose import jwt, jwk, JWTError

# -----------------------------
# Cognito Config
# -----------------------------
COGNITO_REGION = "ap-southeast-2"  # adjust if needed
COGNITO_USERPOOL_ID = "ap-southeast-2_KUuRLDBYK"
COGNITO_CLIENT_ID = "1nc5drgnphkq8i4d2rusnfoa36"

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_BASE = "http://video-api:3000"  # base for backend
SESSIONS = {}  # simple in-memory session store


# -----------------------------
# JWT Decode for Cognito
# -----------------------------
def decode_jwt(token: str):
    try:
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


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password},
        )

        if resp.status_code != 200:
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Invalid credentials"}
            )

        data = resp.json()

        if "challenge" in data:
            # Store temporary session for MFA
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = {
                "username": username,
                "session": data["session"],
                "challenge": data["challenge"],   # <--- add this
            }
            return RedirectResponse(f"/mfa/{session_id}", status_code=303)


        # Normal login flow
        token = data["IdToken"]
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = token
        return RedirectResponse(f"/dashboard/{session_id}", status_code=303)



@app.get("/dashboard/{session_id}", response_class=HTMLResponse)
async def dashboard(request: Request, session_id: str):
    token = SESSIONS.get(session_id)
    if not token:
        return RedirectResponse("/", status_code=303)

    username, role = decode_jwt(token)
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
        async with httpx.AsyncClient() as client:
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


@app.post("/upload/{session_id}")
async def upload(session_id: str, file: UploadFile = File(...)):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        form = {"file": (file.filename, await file.read(), file.content_type)}
        await client.post(f"{API_BASE}/videos/", files=form, headers=headers)
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.post("/delete/{session_id}/{video_id}")
async def delete(session_id: str, video_id: int):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE}/videos/{video_id}", headers=headers)
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.post("/transcode/{session_id}/{video_id}/{fmt}")
async def transcode(session_id: str, video_id: int, fmt: str):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{API_BASE}/videos/{video_id}/transcode",
            json={"format": fmt},
            headers=headers,
        )
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.get("/download/{session_id}/{video_id}")
async def download(session_id: str, video_id: int):
    token = SESSIONS.get(session_id)
    if not token:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/videos/{video_id}/download", headers=headers)
        if resp.status_code != 200:
            return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

        media_type = resp.headers.get("content-type", "application/octet-stream")
        return StreamingResponse(
            io.BytesIO(resp.content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={resp.headers.get('content-disposition', f'video_{video_id}')}"
            },
        )


@app.get("/tasks/{session_id}", response_class=HTMLResponse)
async def tasks_dashboard(request: Request, session_id: str):
    token = SESSIONS.get(session_id)
    if not token:
        return RedirectResponse("/", status_code=303)

    username, role = decode_jwt(token)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    headers = {"Authorization": f"Bearer {token}"}
    tasks = []
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/videos/tasks", headers=headers)
        if resp.status_code == 200:
            tasks = resp.json()

    return templates.TemplateResponse(
        "dashboard_tasks.html",
        {"request": request, "tasks": tasks, "session_id": session_id},
    )


@app.post("/update_metadata/{session_id}/{video_id}")
async def update_metadata(
    session_id: str,
    video_id: int,
    title: str = Form(None),
    description: str = Form(None),
):
    token = SESSIONS.get(session_id)
    if not token:
        return RedirectResponse("/", status_code=303)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    if not payload:
        return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

    async with httpx.AsyncClient() as client:
        await client.put(f"{API_BASE}/videos/{video_id}", json=payload, headers=headers)

    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.get("/logout/{session_id}")
async def logout(session_id: str):
    SESSIONS.pop(session_id, None)
    return RedirectResponse("/", status_code=303)


# Signup page
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# Handle signup form
@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/signup",
            json={"username": username, "password": password, "email": email}
        )
    print("Login response JSON:", resp.json())
    if resp.status_code != 200:
        return templates.TemplateResponse("signup.html", {"request": request, "error": resp.text})
    return RedirectResponse("/confirm", status_code=303)

# Confirm page
@app.get("/confirm", response_class=HTMLResponse)
async def confirm_page(request: Request):
    return templates.TemplateResponse("confirm.html", {"request": request})

# Handle confirmation form
@app.post("/confirm")
async def confirm(request: Request, username: str = Form(...), code: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/confirm",
            json={"username": username, "code": code}
        )
    if resp.status_code != 200:
        return templates.TemplateResponse("confirm.html", {"request": request, "error": resp.text})
    return RedirectResponse("/", status_code=303)


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
    challenge = session_data["challenge"]   # <- pull it back here

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/auth/mfa",
            json={
                "username": username,
                "session": session_token,
                "code": code,
                "challenge": challenge,   # <- send it to backend
            },
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "mfa.html",
            {"request": request, "session_id": session_id, "error": "Invalid code"},
        )

    tokens = resp.json()
    token = tokens["IdToken"]

    # Replace MFA session with real JWT
    SESSIONS[session_id] = token
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

