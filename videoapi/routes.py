from fastapi import APIRouter, Request, BackgroundTasks
from videoapi.controllers import (
    get_all_videos,
    get_video,
    upload_video,
    transcode_video,
    delete_video
)

router = APIRouter()

# List all videos
router.get("/", response_model=list)(get_all_videos)

# Get a specific video by ID
router.get("/{video_id}")(get_video)

# Upload a new video (multipart/form-data)
router.post("/")(upload_video)

# Transcode a video to a new format
@router.post("/{video_id}/transcode")
async def transcode_endpoint(video_id: int, request: Request, background_tasks: BackgroundTasks):
    return await transcode_video(video_id, request, background_tasks)

# Delete a video
router.delete("/{video_id}")(delete_video)