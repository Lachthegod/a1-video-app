from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI()  # must be defined before any decorator
templates = Jinja2Templates(directory="templates")

API_BASE = "http://video-api:3000/videos"  # no trailing slash

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    videos = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/")  # note the slash here
            resp.raise_for_status()
            if resp.content:
                videos = resp.json()
    except Exception as e:
        print("Error fetching videos:", e)
    return templates.TemplateResponse("index.html", {"request": request, "videos": videos})


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        form = {"file": (file.filename, await file.read(), file.content_type)}
        await client.post(f"{API_BASE}/", files=form)  # note slash here
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{video_id}")
async def delete(video_id: int):
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE}/{video_id}")  # no double slash
    return RedirectResponse("/", status_code=303)

@app.post("/transcode/{video_id}/{fmt}")
async def transcode(video_id: int, fmt: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/{video_id}/transcode", json={"format": fmt})  # correct URL
    return RedirectResponse("/", status_code=303)