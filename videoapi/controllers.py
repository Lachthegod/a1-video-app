from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse
from videoapi.models import (
    create_video, get_video_by_id, list_videos, update_status, remove_video
)
import os
import shutil
import ffmpeg  # Python wrapper for FFmpeg

router = APIRouter()


def transcode_video_file(input_path, output_path, output_format):
    try:
        # Force CPU-intensive re-encoding
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec='libx264', acodec='aac', format=output_format)
            .run(overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"Error transcoding video: {e}")
        return False


def get_all_videos():
    try:
        videos = list_videos()
        return JSONResponse(content=jsonable_encoder(videos))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get a video by ID
def get_video(video_id: int):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return JSONResponse(content=jsonable_encoder(video))

async def upload_video(request: Request, current_user: dict):
    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
            
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
        
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Save both owner and user_id in DB
    video_record = create_video(
        filename=file.filename, 
        filepath=file_path,
        owner=current_user["username"],  
        user_id=current_user["id"]      
    )
    return JSONResponse(content=video_record)


# Start transcoding a video (background task)
async def transcode_video(video_id: int, request: Request, background_tasks: BackgroundTasks, current_user: dict):
    data = await request.json()
    output_format = data.get("format")
    if not output_format:
        raise HTTPException(status_code=400, detail="Output format is required")

    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to transcode this video")

        
    input_path = video["filepath"]

    base_name, _ = os.path.splitext(video['filename'])

    output_filename = f"{base_name}_transcoded.{output_format}"
    os.makedirs("uploads", exist_ok=True)
    
    output_path = os.path.join("uploads", output_filename)

    # Update status to transcoding
    update_status(video_id, status="transcoding")
    
    # Run transcoding in background
    background_tasks.add_task(transcode_and_update, video_id, input_path, output_path, output_format)
    return {"message": "Transcoding started", "video_id": video_id}

    
def transcode_and_update(video_id, input_path, output_path, output_format):
    success = transcode_video_file(input_path, output_path, output_format)
    update_status(video_id, status="done" if success else "failed", format=output_format)

    
async def delete_video(video_id: int, current_user: dict):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this video")


    if os.path.exists(video["filepath"]):
        os.remove(video["filepath"])

    result = remove_video(video_id)
    return {"message": "Video deleted" if result["deleted"] else "Failed to delete video"}

# Download a video file (original or transcoded)
def download_video(video_id: int, current_user: dict):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Only allow owner or admin
    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")
    
    # Determine which file to serve (transcoded if exists, else original)
    file_path = video["filepath"]
    base_name, ext = os.path.splitext(file_path)
    
    if video.get("format"):
        transcoded_file = f"{base_name}_transcoded.{video['format']}"
        if os.path.exists(transcoded_file):
            file_path = transcoded_file
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="video/mp4"
    )