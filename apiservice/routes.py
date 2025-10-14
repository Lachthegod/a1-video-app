import asyncio
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from auth import get_current_user
from models import get_video_by_id, update_video_metadata
import os
import json
import boto3
from controllers import (
    get_all_videos,
    upload_video,
    transcode_video,
    delete_video
)
from pstore import load_parameters

router = APIRouter()


parameters = load_parameters()

AWS_REGION = parameters.get("awsregion", "ap-southeast-2")
S3_BUCKET = parameters.get("s3bucket")


s3_client = boto3.client("s3", region_name=AWS_REGION)


@router.get("/")
async def list_videos(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "created_at",
    order: str = "desc",
    status: str | None = None,
    owner: str | None = None,
    search: str | None = None,
):
    videos = get_all_videos(user_id=None if current_user["role"]=="admin" else current_user["id"]) 

    if current_user["role"] != "admin":
        videos = [v for v in videos if v["owner"] == current_user["username"]]

    if status:
        videos = [v for v in videos if v["status"] == status]
    if owner:
        videos = [v for v in videos if v["owner"] == owner]
    if search:
        videos = [v for v in videos if search.lower() in v["filename"].lower()]

    # if videos and sort_by in videos[0]:
    #     videos.sort(key=lambda v: v.get(sort_by), reverse=(order == "desc"))

    if videos:
        videos.sort(
            key=lambda v: v.get(sort_by) or "",  # fallback so None won't break sorting
            reverse=(order == "desc")
        )

    return {
        "total": len(videos),
        "skip": skip,
        "limit": limit,
        "items": videos[skip : skip + limit],
    }



@router.get("/{video_id}")
async def get_video_route(video_id: str, current_user: dict = Depends(get_current_user)):
 
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
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
async def transcode_endpoint(video_id: str,request: Request,background_tasks: BackgroundTasks,current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to transcode this video")
    return await transcode_video(video_id, request, background_tasks, current_user)


@router.delete("/{video_id}")
async def delete_video_route(video_id: str, current_user: dict = Depends(get_current_user)):
    return await delete_video(video_id, current_user)


@router.get("/{video_id}/download")
async def download_video(video_id: str, current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")
    
    #S3 presigned URL
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": video["filepath"]}, 
            ExpiresIn=3600
        )
        return {"download_url": presigned_url}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not generate download link")



@router.put("/{video_id}")
async def update_video_route(video_id: str, metadata: dict = Body(...), current_user: dict = Depends(get_current_user)):
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this video")

    updated_video = update_video_metadata(current_user['role'],current_user["id"],video_id, metadata)
    if not updated_video:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    return {"message": "Video updated", "video": updated_video}


@router.get("/{video_id}/progress/stream")
async def stream_progress(video_id: str, current_user: dict = Depends(get_current_user)):
    async def event_generator():
        try:
            while True:
                video = get_video_by_id(current_user['role'], current_user['id'], video_id)
                if video:
                    yield f"data: {json.dumps(video)}\n\n"
                await asyncio.sleep(2)  #Stream updates 2s
        except asyncio.CancelledError:
           
            print(f"Client disconnected from video {video_id} progress stream")
            return

    return StreamingResponse(event_generator(), media_type="text/event-stream")