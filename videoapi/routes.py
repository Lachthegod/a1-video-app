from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status, Body
from fastapi.responses import FileResponse
from videoapi.auth import authenticate_user, generate_access_token, get_current_user
from videoapi.models import get_video_by_id, update_video_metadata
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


# Public endpoint
@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_access_token(username)
    return {"authToken": token}


# Admin endpoint
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


# Video endpoints,JWT protected
@router.get("/")
async def list_videos(current_user: dict = Depends(get_current_user)):
    """List videos with role-based filtering"""
    all_videos = get_all_videos()
    if current_user["role"] == "admin":
        return all_videos
    return [v for v in all_videos if v["owner"] == current_user["username"]]


@router.get("/{video_id}")
async def get_video_route(video_id: int, current_user: dict = Depends(get_current_user)):
    """Fetch a specific video, enforcing ownership/admin access"""
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this video")
    return video


@router.post("/")
async def upload_video_route(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return await upload_video(request, current_user)


@router.post("/{video_id}/transcode")
async def transcode_endpoint(video_id: int,request: Request,background_tasks: BackgroundTasks,current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to transcode this video")
    return await transcode_video(video_id, request, background_tasks, current_user)


@router.delete("/{video_id}")
async def delete_video_route(video_id: int,current_user: dict = Depends(get_current_user)):
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
    
    return FileResponse(
        path=video["filepath"], 
        filename=os.path.basename(video["filepath"]), 
        media_type="video/mp4"
    )


@router.put("/{video_id}")
async def update_video_route(video_id: int, metadata: dict = Body(...), current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this video")

    updated_video = update_video_metadata(video_id, metadata)
    if not updated_video:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    return {"message": "Video updated", "video": updated_video}
