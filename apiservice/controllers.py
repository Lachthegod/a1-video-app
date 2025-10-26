import json
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from models import (
    create_video, get_video_by_id, list_videos, update_status, remove_video, all_videos, update_status_progress
)
import subprocess
import re
import ffmpeg
import tempfile
import os
import uuid
import boto3

from pstore import load_parameters

sqs = boto3.client('sqs', region_name='ap-southeast-2')
QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/901444280953/n11715910-a2"

router = APIRouter()

parameters = load_parameters()

AWS_REGION = parameters.get("awsregion", "ap-southeast-2")
S3_BUCKET = parameters.get("s3bucket")





s3_client = boto3.client("s3", region_name=AWS_REGION)


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



def get_all_videos(user_id=None):
    if user_id:
        videos = list_videos(user_id)
    else:
        videos = all_videos()
    return jsonable_encoder(videos)


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




async def transcode_video(video_id, request: Request, background_tasks: BackgroundTasks, current_user: dict):
    data = await request.json()
    output_format = data.get("format")
    if not output_format:
        raise HTTPException(status_code=400, detail="Output format is required")

    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to transcode this video")

    input_key = video["filepath"]
    base_name, _ = os.path.splitext(video["filename"])
    # output_key = f"transcoded/{base_name}_{output_format}.{output_format}"


    

    message = {
        "video_id": video_id,
        "input_key": input_key,
        "filename": base_name,
        "output_format": output_format,
        "user_id": current_user["id"]
    }

    # Send to SQS
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    update_status(current_user["id"], video_id, status="transcoding")
    return {"message": "Transcoding started", "video_id": video_id}



async def delete_video(video_id, current_user: dict):
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this video")

    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=video["filepath"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")

    result = remove_video(current_user['role'],current_user["id"], video_id)
    return {"message": "Video deleted" if result else "Failed to delete video"}



def download_video(video_id, current_user: dict):
    video = get_video_by_id(current_user['role'], current_user['id'], video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to download this video")

    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": video["filepath"]},
            ExpiresIn=3600 
        )
        return {"download_url": presigned_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download link: {str(e)}")
