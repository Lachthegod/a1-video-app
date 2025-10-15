import os
from fastapi import FastAPI
from routes_auth import router as api_router

app = FastAPI(
    title="Video Stream API",
    description="API for streaming services",
    version="0.0.1",
)


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)