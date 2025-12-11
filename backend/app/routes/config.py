"""
Config Routes
API endpoints for integrations configuration (Linear, Slack)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.linear_service import linear_service
from app.services.slack_service import slack_service

router = APIRouter(prefix="/api/config", tags=["Configuration"])


# ============== Linear Integration ==============

@router.get("/linear/teams")
async def get_linear_teams() -> List[Dict]:
    """Get all Linear teams"""
    try:
        teams = await linear_service.get_teams()
        return teams
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Linear teams: {str(e)}")


@router.get("/linear/teams/{team_id}/members")
async def get_linear_team_members(team_id: str) -> List[Dict]:
    """Get members of a Linear team"""
    try:
        members = await linear_service.get_team_members(team_id)
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team members: {str(e)}")


@router.get("/linear/teams/{team_id}/issues")
async def get_linear_team_issues(team_id: str, active_only: bool = True) -> List[Dict]:
    """Get issues for a Linear team"""
    try:
        issues = await linear_service.get_team_issues(team_id, active_only)
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")


@router.get("/linear/teams/{team_id}/states")
async def get_linear_workflow_states(team_id: str) -> List[Dict]:
    """Get workflow states for a Linear team"""
    try:
        states = await linear_service.get_workflow_states(team_id)
        return states
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow states: {str(e)}")


# ============== Slack Integration ==============

@router.get("/slack/channels")
async def get_slack_channels() -> List[Dict]:
    """Get all Slack channels"""
    try:
        channels = await slack_service.get_channels()
        return [
            {
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False)
            }
            for ch in channels
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Slack channels: {str(e)}")


@router.get("/slack/users")
async def get_slack_users() -> List[Dict]:
    """Get all Slack users"""
    try:
        users = await slack_service.get_users()
        return [
            {
                "id": u.get("id"),
                "name": u.get("real_name") or u.get("name"),
                "email": u.get("profile", {}).get("email"),
                "avatar": u.get("profile", {}).get("image_48")
            }
            for u in users
            if not u.get("deleted") and not u.get("is_bot")
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Slack users: {str(e)}")


# ============== Health Check ==============

@router.get("/health")
async def health_check() -> Dict:
    """Check integration health status"""
    from app.config import settings
    
    health = {
        "linear": False,
        "slack": False,
        "elevenlabs": False,
        "jitsi": False
    }
    
    # Check Linear
    try:
        teams = await linear_service.get_teams()
        health["linear"] = len(teams) > 0
    except:
        pass
    
    # Check Slack
    try:
        channels = await slack_service.get_channels()
        health["slack"] = len(channels) > 0
    except:
        pass
    
    # Check ElevenLabs - just verify API key is configured
    try:
        if settings.ELEVENLABS_API_KEY and len(settings.ELEVENLABS_API_KEY) > 10:
            health["elevenlabs"] = True
    except:
        pass
    
    # Check Jitsi - verify app ID and private key are configured
    try:
        if settings.JITSI_APP_ID and settings.JITSI_PRIVATE_KEY:
            health["jitsi"] = True
    except:
        pass
    
    return health

