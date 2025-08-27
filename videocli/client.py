from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import jwt
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_BASE = "http://video-api:3000/videos"
SESSIONS = {}  # {session_id: token}
SECRET_KEY = "supersecretkey"  # must match backend auth.py
ALGORITHM = "HS256"


def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "user")
        return username, role
    except jwt.PyJWTError:
        return None, None


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/login", json={"username": username, "password": password})
        if resp.status_code != 200:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
        token = resp.json()["authToken"]

    # generate random session ID
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
    videos = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/", headers=headers)
            all_videos = resp.json()

            # FILTER VIDEOS
            if role == "admin":
                videos = all_videos  # admin sees everything
            else:
                videos = [v for v in all_videos if v["owner"] == username]

    except Exception as e:
        print("Error fetching videos:", e)

    template_name = "dashboard_admin.html" if role == "admin" else "dashboard_user.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "videos": videos,
        "session_id": session_id,
        "username": username,
        "role": role
    })


@app.post("/upload/{session_id}")
async def upload(session_id: str, file: UploadFile = File(...)):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        form = {"file": (file.filename, await file.read(), file.content_type)}
        await client.post(f"{API_BASE}/", files=form, headers=headers)
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.post("/delete/{session_id}/{video_id}")
async def delete(session_id: str, video_id: int):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE}/{video_id}", headers=headers)
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)


@app.post("/transcode/{session_id}/{video_id}/{fmt}")
async def transcode(session_id: str, video_id: int, fmt: str):
    token = SESSIONS.get(session_id)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/{video_id}/transcode", json={"format": fmt}, headers=headers)
    return RedirectResponse(f"/dashboard/{session_id}", status_code=303)

