import os
from fastapi import FastAPI
from videoapi.routes import router as api_router
from videoapi import routes_auth  # your Cognito signup/login routes

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Video Stream API",
    description="API for streaming services",
    version="0.0.1",
)

# Mount routers AFTER app is created
app.include_router(api_router, prefix="/videos")
app.include_router(routes_auth.router, prefix="/auth")  # <- needs .router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
