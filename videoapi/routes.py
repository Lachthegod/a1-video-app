from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status, Body
from videoapi.auth import authenticate_user, generate_access_token, get_current_user
from videoapi.controllers import (
    get_all_videos,
    get_video,
    upload_video,
    transcode_video,
    delete_video
)

router = APIRouter()

# List all videos (public)
router.get("/", response_model=list)(get_all_videos)

# Get a specific video by ID (public)
router.get("/{video_id}")(get_video)

# Upload a new video (requires login)
@router.post("/")
async def upload_video_route(
    request: Request,
    current_user: dict = Depends(get_current_user)  # protect with JWT
):
    return await upload_video(request, current_user)

# Transcode a video (requires login)
@router.post("/{video_id}/transcode")
async def transcode_endpoint(
    video_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    return await transcode_video(video_id, request, background_tasks, current_user)

# Delete a video (admin only)
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

@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_access_token(username)
    return {"authToken": token}