import os
import shutil
from fastapi import FastAPI
from videoapi.routes import router as api_router


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Video Stream API",
    description="API for streaming services",
    version="0.0.1",
)

# Prefix is used to group routes under a common path
app.include_router(api_router, prefix="/videos")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=3000)