from db.db import get_connection
import datetime

def create_video(filename, filepath, owner=None, user_id=None, status="uploaded", format=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos (filename, filepath, status, format, owner, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (filename, filepath, status, format, owner, user_id)
    )
    conn.commit()
    video_id = cursor.lastrowid
    conn.close()
    return {
        "id": video_id,
        "filename": filename,
        "status": status,
        "format": format,
        "owner": owner,
        "user_id": user_id
    }

def get_video_by_id(video_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return dict(zip(columns, row)) if row else None

def list_videos(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM videos WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM videos")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    videos = []
    for row in rows:
        video = dict(zip(columns, row))
        for key, value in video.items():
            if isinstance(value, datetime.datetime):
                video[key] = value.isoformat() 
        videos.append(video)

    return videos



def update_status(video_id, status, format=None):
    conn = get_connection()
    cursor = conn.cursor()
    if format:
        cursor.execute(
            "UPDATE videos SET status = ?, format = ? WHERE id = ?",
            (status, format, video_id)
        )
    else:
        cursor.execute(
            "UPDATE videos SET status = ? WHERE id = ?",
            (status, video_id)
        )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return {"updated": updated}
    



    
def remove_video(video_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return {"deleted": deleted}

