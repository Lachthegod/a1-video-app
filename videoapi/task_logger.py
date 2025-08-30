import json
from datetime import datetime
import os

# File path for storing task logs
LOG_FILE = os.environ.get("TASK_LOG_FILE", "transcode_tasks.json")

# Ensure the file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)


def log_transcoding_task(video_id: int, user_id: int, format: str, status: str, error: str = None):
    """
    Log a video transcoding task to a local JSON file.
    """
    item = {
        "video_id": video_id,
        "user_id": user_id,
        "format": format,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    if error:
        item["error"] = error

    # Read current logs
    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    # Append new task
    logs.append(item)

    # Save back
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


