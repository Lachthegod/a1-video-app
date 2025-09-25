from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from videoapi.task_logger import log_transcoding_task
from videoapi.models import (
    create_video, get_video_by_id, list_videos, update_status, remove_video, all_videos
)

import ffmpeg
import tempfile
import os
import uuid
import boto3

router = APIRouter()

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "n11715910-a2")

s3_client = boto3.client("s3", region_name=AWS_REGION)


# ---------- Helper: Transcoding ----------
def transcode_video_file(input_path, output_path, output_format="mp4"):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec="libx264", acodec="aac", format=output_format)
            .run(overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"Error transcoding video: {e}")
        return False


# ---------- List + Get ----------
# def get_all_videos():
#     try:
#         videos = list_videos()
#         return jsonable_encoder(videos)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

def get_all_videos(user_id=None):
    if user_id:
        videos = list_videos(user_id)
    else:
        videos = all_videos()
    return jsonable_encoder(videos)



# def get_video(video_id: int):
#     video = get_video_by_id(current_user['id'], video_id)
#     if not video:
#         raise HTTPException(status_code=404, detail="Video not found")
#     return JSONResponse(content=jsonable_encoder(video))


# ---------- Upload (Presigned) ----------
async def upload_video(request: Request, current_user: dict):
    data = await request.json()
    filename = data.get("filename")
    content_type = data.get("content_type")
    if not filename or not content_type:
        raise HTTPException(status_code=400, detail="Missing filename or content_type")

    object_key = f"uploads/{current_user['id']}/{filename}"

    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": object_key, "ContentType": content_type},
        ExpiresIn=3600
    )

    video_record = create_video(
        filename=filename,
        filepath=object_key,
        owner=current_user["username"],
        user_id=current_user["id"],
        status="Uploaded"
    )

    return {"upload_url": presigned_url, "object_key": object_key, "video_record": video_record}




# ---------- Transcode ----------
async def transcode_video(video_id: int, request: Request, background_tasks: BackgroundTasks, current_user: dict):
    data = await request.json()
    output_format = data.get("format")
    if not output_format:
        raise HTTPException(status_code=400, detail="Output format is required")

    video = get_video_by_id(current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to transcode this video")

    input_key = video["filepath"]
    base_name, _ = os.path.splitext(video["filename"])
    output_key = f"transcoded/{base_name}_{output_format}.{output_format}"

    update_status(video_id, status="transcoding")
    background_tasks.add_task(
        transcode_and_update, video_id, input_key, output_key, output_format, current_user["id"]
    )
    return {"message": "Transcoding started", "video_id": video_id}


def transcode_and_update(video_id, input_key, output_key, output_format, user_id):
    try:
        # Download input from S3
        with tempfile.NamedTemporaryFile(delete=False) as tmp_in:
            s3_client.download_file(S3_BUCKET, input_key, tmp_in.name)
            input_path = tmp_in.name

        # Prepare output temp file
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}")
        output_path = tmp_out.name
        tmp_out.close()

        success = transcode_video_file(input_path, output_path, output_format)

        if success:
            s3_client.upload_file(output_path, S3_BUCKET, output_key)
            update_status(video_id, status="done", format=output_format)
            log_transcoding_task(video_id, user_id=user_id, format=output_format, status="done")
        else:
            update_status(video_id, status="failed")
            log_transcoding_task(video_id, user_id=user_id, format=output_format, status="failed", error="Transcoding failed")

    except Exception as e:
        update_status(video_id, status="failed")
        log_transcoding_task(video_id, user_id=user_id, format=output_format, status="failed", error=str(e))


# ---------- Delete ----------
async def delete_video(video_id: int, current_user: dict):
    video = get_video_by_id(current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this video")

    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=video["filepath"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")

    result = remove_video(current_user["id"], video_id)
    return {"message": "Video deleted" if result else "Failed to delete video"}



# ---------- Download (via pre-signed URL) ----------
def download_video(video_id: int, current_user: dict):
    video = get_video_by_id(current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")

    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": video["filepath"]},
            ExpiresIn=3600  # 1 hour
        )
        return {"download_url": presigned_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download link: {str(e)}")
