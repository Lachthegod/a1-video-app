#from db.db import get_connection
# import datetime

# def create_video(filename, filepath, owner=None, user_id=None, status="uploaded", format=None):
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT INTO videos (filename, filepath, status, format, owner, user_id) VALUES (?, ?, ?, ?, ?, ?)",
#         (filename, filepath, status, format, owner, user_id)
#     )
#     conn.commit()
#     video_id = cursor.lastrowid
#     conn.close()
#     return {
#         "id": video_id,
#         "filename": filename,
#         "status": status,
#         "format": format,
#         "owner": owner,
#         "user_id": user_id
#     }

# def get_video_by_id(video_id):
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
#     row = cursor.fetchone()
#     columns = [desc[0] for desc in cursor.description]
#     conn.close()
#     return dict(zip(columns, row)) if row else None

# def list_videos(user_id=None):
#     conn = get_connection()
#     cursor = conn.cursor()
#     if user_id:
#         cursor.execute("SELECT * FROM videos WHERE user_id = ?", (user_id,))
#     else:
#         cursor.execute("SELECT * FROM videos")
#     rows = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]
#     conn.close()

#     videos = []
#     for row in rows:
#         video = dict(zip(columns, row))
#         for key, value in video.items():
#             if isinstance(value, datetime.datetime):
#                 video[key] = value.isoformat() 
#         videos.append(video)

#     return videos



# def update_status(video_id, status, format=None):
#     conn = get_connection()
#     cursor = conn.cursor()
#     if format:
#         cursor.execute(
#             "UPDATE videos SET status = ?, format = ? WHERE id = ?",
#             (status, format, video_id)
#         )
#     else:
#         cursor.execute(
#             "UPDATE videos SET status = ? WHERE id = ?",
#             (status, video_id)
#         )
#     conn.commit()
#     updated = cursor.rowcount > 0
#     conn.close()
#     return {"updated": updated}
    



    
# def remove_video(video_id):
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
#     conn.commit()
#     deleted = cursor.rowcount > 0
#     conn.close()
#     return {"deleted": deleted}


# def update_video_metadata(video_id, metadata: dict):
#     allowed_fields = ["title", "description"]
#     updates = {k: v for k, v in metadata.items() if k in allowed_fields}

#     if not updates:
#         return None

#     set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
#     values = list(updates.values())
#     values.append(video_id)

#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute(f"UPDATE videos SET {set_clause} WHERE id = ?", values)
#     conn.commit()
#     updated = cursor.rowcount > 0
#     cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
#     row = cursor.fetchone()
#     columns = [desc[0] for desc in cursor.description]
#     conn.close()

#     return dict(zip(columns, row)) if row else None

import boto3
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
TABLE_NAME = f"n11715910-a2"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)


def create_video(filename, filepath, title=None, description=None, owner=None, user_id=None, status="uploaded", format=None):
    video_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    item = {
        "user_id": user_id or "anonymous",
        "video_id": video_id,
        "filename": filename,
        "filepath": filepath,
        "title": title or "",
        "description": description or "",
        "status": status,
        "format": format or "",
        "owner": owner or "",
        "created_at": created_at,
    }

    try:
        table.put_item(Item=item)
        return item
    except ClientError as e:
        raise Exception(f"Error creating video: {e}")


def get_video_by_id(user_id, video_id):
    try:
        resp = table.get_item(Key={"user_id": user_id, "video_id": video_id})
        return resp.get("Item")
    except ClientError as e:
        raise Exception(f"Error retrieving video: {e}")


def list_videos(user_id):
    try:
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user_id)
        )
        return resp.get("Items", [])
    except ClientError as e:
        raise Exception(f"Error listing videos: {e}")
    
def all_videos():
    try:
        resp = table.scan()
        return resp.get("Items", [])
    except ClientError as e:
        raise Exception(f"Error listing all videos: {e}")


def update_status(user_id, video_id, status):
    try:
        resp = table.update_item(
            Key={"user_id": user_id, "video_id": video_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":val": status},
            ReturnValues="ALL_NEW"
        )
        return resp.get("Attributes")
    except ClientError as e:
        raise Exception(f"Error updating video status: {e}")


def update_video_metadata(user_id, video_id, format=None, filename=None, title=None, description=None):
    update_expr = []
    expr_attr_vals = {}
    expr_attr_names = {}

    if format:
        update_expr.append("#f = :f")
        expr_attr_vals[":f"] = format
        expr_attr_names["#f"] = "format"

    if filename:
        update_expr.append("#fn = :fn")
        expr_attr_vals[":fn"] = filename
        expr_attr_names["#fn"] = "filename"

    if title:
        update_expr.append("#t = :t")
        expr_attr_vals[":t"] = title
        expr_attr_names["#t"] = "title"

    if description:
        update_expr.append("#d = :d")
        expr_attr_vals[":d"] = description
        expr_attr_names["#d"] = "description"

    if not update_expr:
        return get_video_by_id(user_id, video_id)

    try:
        resp = table.update_item(
            Key={"user_id": user_id, "video_id": video_id},
            UpdateExpression="SET " + ", ".join(update_expr),
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_vals,
            ReturnValues="ALL_NEW"
        )
        return resp.get("Attributes")
    except ClientError as e:
        raise Exception(f"Error updating video metadata: {e}")


def remove_video(user_id, video_id):
    try:
        table.delete_item(Key={"user_id": user_id, "video_id": video_id})
        return True
    except ClientError as e:
        raise Exception(f"Error deleting video: {e}")
