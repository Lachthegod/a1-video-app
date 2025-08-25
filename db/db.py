import os
import mariadb
import sys
import time

DB_HOST = os.environ.get("DB_HOST", "video-db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "pass")
DB_NAME = os.environ.get("DB_NAME", "videosdb")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_connection(retries=5, delay=3):
    for i in range(retries):
        try:
            conn = mariadb.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT
            )
            return conn
        except mariadb.Error as e:
            print(f"DB connection failed ({i+1}/{retries}): {e}")
            time.sleep(delay)
    print("Could not connect to MariaDB after multiple attempts.")
    sys.exit(1)



def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INT PRIMARY KEY AUTO_INCREMENT,
                filename VARCHAR(255) NOT NULL,
                filepath VARCHAR(500) NOT NULL,  -- path on disk or cloud
                status VARCHAR(50) DEFAULT 'uploaded',  -- uploaded, transcoding, done, failed
                format VARCHAR(20),
                user_id INT,  -- optional for multi-user system
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Database initialized and videos table ensured.")
    except Exception as e:
        print(f"DB init failed: {e}")
    finally:
        conn.close()

init_db()