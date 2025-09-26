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

    
def get_video_by_id(user_role, user_id, video_id):
    try:
        if user_role == "admin":
            # Admin: scan all items until matching video_id
            resp = table.scan(
                FilterExpression="video_id = :vid",
                ExpressionAttributeValues={":vid": video_id}
            )
            items = resp.get("Items", [])
            return items[0] if items else None
        else:
            # Normal user: lookup by composite key
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
    

def update_status_progress(user_id, video_id, status, progress=None, format=None):

    update_expr = ["#s = :s"]
    expr_attr_vals = {":s": status}
    expr_attr_names = {"#s": "status"}

    if progress is not None:
        update_expr.append("#p = :p")
        expr_attr_vals[":p"] = progress
        expr_attr_names["#p"] = "progress"

    if format is not None:
        update_expr.append("#f = :f")
        expr_attr_vals[":f"] = format
        expr_attr_names["#f"] = "format"

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
        raise Exception(f"Error updating video status/progress: {e}")



def update_video_metadata(user_role, user_id, video_id, format=None, filename=None, title=None, description=None):
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
        return get_video_by_id(user_role, user_id, video_id)

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
