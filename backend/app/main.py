"""
StandupAI - AI-Powered Standup Automation Platform
Main FastAPI Application
"""

import time
import jwt
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app.config import settings
from app.database import init_db
from app.routes import standup, config, analytics
from app.services.scheduler_service import scheduler_service
from app.services.voice_endpoint import (
    handle_voice_websocket,
    get_active_voice_session_count,
    get_voice_session_status
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("standupai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("Starting StandupAI...")
    init_db()
    scheduler_service.start()
    yield
    # Shutdown
    print("Shutting down StandupAI...")
    scheduler_service.stop()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Standup Automation Platform - Automate your daily standups with Linear, Slack, and Jitsi integration",
    version=settings.APP_VERSION,
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(standup.router)
app.include_router(config.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============== Voice Endpoints ==============

@app.websocket("/standup/{standup_id}/voice")
async def standup_voice_websocket(
    websocket: WebSocket, 
    standup_id: str,
    team_id: str = None,
    slack_channel_id: str = None
):
    """Real-time voice conversation WebSocket for standups
    
    Query params:
        team_id: Linear team ID for creating escalation tickets
        slack_channel_id: Slack channel to post summary to
    """
    print(f"Voice WebSocket connection request for standup: {standup_id}")
    print(f"  team_id: {team_id}, slack_channel_id: {slack_channel_id}")
    try:
        await handle_voice_websocket(
            websocket=websocket, 
            standup_id=standup_id,
            team_id=team_id,
            slack_channel_id=slack_channel_id
        )
    except Exception as e:
        print(f"Voice endpoint error for standup {standup_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass


@app.get("/voice/sessions")
async def get_voice_sessions():
    """Get status of all active voice sessions"""
    return {
        "active_sessions": get_active_voice_session_count(),
        "timestamp": time.time()
    }


@app.get("/voice/sessions/{standup_id}")
async def get_voice_session(standup_id: str):
    """Get status of a specific voice session"""
    status = get_voice_session_status(standup_id)
    if not status:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return status


# ============== Jitsi JWT Endpoints ==============

def _get_jitsi_private_key():
    """Load Jitsi private key from config"""
    if not settings.JITSI_PRIVATE_KEY:
        return None
    
    try:
        # Handle escaped newlines
        pem = settings.JITSI_PRIVATE_KEY.replace("\\n", "\n").encode()
        key = serialization.load_pem_private_key(
            pem, password=None, backend=default_backend()
        )
        return key
    except Exception as e:
        print(f"Failed to load Jitsi private key: {e}")
        return None


@app.post("/jitsi/jwt")
async def mint_jitsi_jwt(body: dict):
    """Mint a JWT token for Jitsi meeting authentication"""
    # Validate required fields
    required = ["room", "user"]
    for key in required:
        if key not in body:
            return JSONResponse({"error": f"Missing field: {key}"}, status_code=400)
    
    # Validate configuration
    if not all([settings.JITSI_APP_ID, settings.JITSI_PRIVATE_KEY]):
        return JSONResponse(
            {"error": "Jitsi not configured"},
            status_code=500
        )
    
    # Load private key
    private_key = _get_jitsi_private_key()
    if not private_key:
        return JSONResponse(
            {"error": "Invalid Jitsi private key"},
            status_code=500
        )
    
    room = body["room"]
    user = body["user"]
    ttl_sec = body.get("ttlSec", 3600)  # Default 1 hour
    features = body.get("features", {"transcription": True})
    
    now = int(time.time())
    claims = {
        "iss": "chat",
        "sub": settings.JITSI_APP_ID,
        "aud": "jitsi",
        "room": room,
        "exp": now + ttl_sec,
        "nbf": now,
        "context": {"user": user, "features": features},
    }
    
    try:
        headers = {}
        if settings.JITSI_PUBLIC_KEY_ID:
            headers["kid"] = settings.JITSI_PUBLIC_KEY_ID
        
        jwt_token = jwt.encode(
            claims,
            private_key,
            algorithm="RS256",
            headers=headers if headers else None
        )
        
        full_room = f"{settings.JITSI_APP_ID}/{room}"
        
        print(f"JWT minted for room: {full_room}")
        
        return JSONResponse({
            "domain": settings.JITSI_DOMAIN,
            "room": full_room,
            "jwt": jwt_token
        })
        
    except Exception as e:
        print(f"JWT signing failed: {e}")
        return JSONResponse(
            {"error": f"Failed to sign JWT: {str(e)}"},
            status_code=500
        )


@app.get("/api/jitsi/config")
async def get_jitsi_config():
    """Get Jitsi configuration for frontend"""
    return {
        "domain": settings.JITSI_DOMAIN,
        "appId": settings.JITSI_APP_ID,
        "configured": bool(settings.JITSI_APP_ID and settings.JITSI_PRIVATE_KEY)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


