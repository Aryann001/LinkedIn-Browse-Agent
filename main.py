import asyncio
import sys

# FIX: Add this check right at the top of main.py
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.limiter import limiter
from routers import agent, admin  # <-- ADD ADMIN
from config.database import init_db
from utils.connection_manager import manager
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="LinkedIn Browse Agent",
    description="Browses LinkedIn, generates comments, and summarizes the feed.",
    version="1.0.0",
)

# --- Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND")], # Allow Next.js
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Event Handlers ---
@app.on_event("startup")
async def on_startup():
    print("Server starting up...")
    await init_db()
    print("Database connection initialized.")

# --- Routers ---
app.include_router(agent.router)
app.include_router(admin.router)  # <-- ADD ADMIN ROUTER

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
@limiter.limit("5/second")
def health_check(request: Request):
    return {"success": True, "message": "Server is Healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)