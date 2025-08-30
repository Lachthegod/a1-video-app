from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status, Body
from fastapi.responses import FileResponse
from videoapi.auth import authenticate_user, generate_access_token, get_current_user
from videoapi.models import get_video_by_id
import os
import json
from videoapi.controllers import (
    get_all_videos,
    get_video,
    upload_video,
    transcode_video,
    delete_video
)

router = APIRouter()
router.get("/", response_model=list)(get_all_videos)
router.get("/{video_id}")(get_video)


@router.post("/")
async def upload_video_route(
    request: Request,
    current_user: dict = Depends(get_current_user)  #JWT prtection and transcode, delete (admin)
):
    return await upload_video(request, current_user)

@router.post("/{video_id}/transcode")
async def transcode_endpoint(
    video_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    return await transcode_video(video_id, request, background_tasks, current_user)

@router.delete("/{video_id}")
async def delete_video_route(
    video_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only can delete videos"
        )
    return await delete_video(video_id)

@router.get("/{video_id}/download")
async def download_video(video_id: int, current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")
    
    if not os.path.exists(video["filepath"]):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(path=video["filepath"], filename=os.path.basename(video["filepath"]), media_type="video/mp4")


@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_access_token(username)
    return {"authToken": token}

@router.get("/tasks")
async def get_transcoding_tasks(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    LOG_FILE = "/usr/src/app/transcode_tasks.json"
    try:
        with open(LOG_FILE, "r") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        tasks = []

    return tasks