from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse
from videoapi.task_logger import log_transcoding_task
from videoapi.models import (
    create_video, get_video_by_id, list_videos, update_status, remove_video
)
import os
import shutil
import ffmpeg  

router = APIRouter()


def transcode_video_file(input_path, output_path, output_format):
    try:
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

    video_record = create_video(
        filename=file.filename, 
        filepath=file_path,
        owner=current_user["username"],  
        user_id=current_user["id"]      
    )
    return JSONResponse(content=video_record)




# Start transcoding a video 
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
    update_status(video_id, status="transcoding")
    background_tasks.add_task(transcode_and_update, video_id, input_path, output_path, output_format, current_user["id"])
    return {"message": "Transcoding started", "video_id": video_id}

    
def transcode_and_update(video_id, input_path, output_path, output_format, user_id):
    try:
        success = transcode_video_file(input_path, output_path, output_format)
        status = "done" if success else "failed"
        error_msg = None if success else "Transcoding failed"
        update_status(video_id, status=status, format=output_format)
        log_transcoding_task(video_id, user_id=user_id, format=output_format, status=status, error=error_msg)
    except Exception as e:
        update_status(video_id, status="failed")
        log_transcoding_task(video_id, user_id=user_id, format=output_format, status="failed", error=str(e))

    
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

#Download, need to fix for .mov
def download_video(video_id: int, current_user: dict):
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")

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