import boto3
import json
import subprocess
import tempfile
import os
import requests

REGION = "ap-southeast-2"
QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/901444280953/n11715910-a2"
S3_BUCKET = "n11715910-a2"
API_BASE = "https://transcoding-n11715910.cab432.com"   # your Route53/ALB domain

sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def update_api(video_id, status, progress=0, output_format=None):
    try:
        payload = {"status": status, "progress": progress}
        if output_format:
            payload["format"] = output_format
        r = requests.post(f"{API_BASE}/videos/{video_id}/status", json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to notify API: {e}")

def process_message(task):
    video_id = task["video_id"]
    output_format = task["output_format"]
    filename = task["filename"]
    input_key = task["input_key"]
    user_id = task["user_id"]

    update_api(video_id, "transcoding", 0)

    with tempfile.NamedTemporaryFile(delete=False) as tmp_in:
        s3.download_file(S3_BUCKET, input_key, tmp_in.name)
        input_path = tmp_in.name

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}").name
    output_key = f"transcoded/{filename}_{output_format}.{output_format}"

    process = subprocess.run(
        ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-y", output_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if process.returncode == 0:
        s3.upload_file(output_path, S3_BUCKET, output_key)
        update_api(video_id, "done", 100, output_format)
    else:
        update_api(video_id, "failed", 0)

    os.remove(input_path)
    os.remove(output_path)


def poll_queue():
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=600
        )
        messages = response.get('Messages', [])

        #delete message from SQS
        if messages:
            for msg in messages:
                task = json.loads(msg["Body"])
                try:
                    process_message(task)
                except Exception as e:
                    print(f"[ERROR] Processing failed for {task['video_id']}: {e}")
                finally:
                    # Always delete message to avoid retries
                    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])


if __name__ == "__main__":
    poll_queue()

# def poll_queue():
#     empty_polls = 0
#     max_empty_polls = 6  # e.g. 6 × 10s = 1 minute idle before exit

#     while True:
#         response = sqs.receive_message(
#             QueueUrl=QUEUE_URL,
#             MaxNumberOfMessages=1,
#             WaitTimeSeconds=10
#         )
#         messages = response.get('Messages', [])
#         if messages:
#             empty_polls = 0  # reset since we have work
#             for msg in messages:
#                 task = json.loads(msg["Body"])
#                 process_message(task)
#                 sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
#         else:
#             empty_polls += 1
#             if empty_polls >= max_empty_polls:
#                 print("Queue idle for too long. Exiting worker...")
#                 break  # let ECS terminate task normally
#             time.sleep(10)








       