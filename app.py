import os
import uvicorn
from fastapi import FastAPI
from api.routes import router as api_router
from api import routes_auth

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Video Stream API",
    description="API for streaming services",
    version="0.0.1",
)

app.include_router(api_router, prefix="/videos")
app.include_router(routes_auth.router, prefix="/auth")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
