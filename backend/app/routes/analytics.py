"""
Analytics Routes
API endpoints for dashboard statistics and analytics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime, timedelta

from app.database import get_db
from app.models import StandupConfig, Standup, IssueUpdate, PMSummary
from app.schemas import DashboardStats, StandupAnalytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard overview statistics"""
    
    # Total standups
    total_standups = db.query(func.count(Standup.id)).scalar() or 0
    
    # Completed standups
    completed_standups = db.query(func.count(Standup.id)).filter(
        Standup.status == "completed"
    ).scalar() or 0
    
    # Total issues discussed
    total_issues = db.query(func.count(IssueUpdate.id)).scalar() or 0
    
    # Blocked issues count
    blocked_count = db.query(func.count(IssueUpdate.id)).filter(
        IssueUpdate.status == "blocked"
    ).scalar() or 0
    
    # Escalations created
    escalations_count = db.query(func.count(IssueUpdate.id)).filter(
        IssueUpdate.escalation_ticket_id.isnot(None)
    ).scalar() or 0
    
    # Average duration
    avg_duration = db.query(func.avg(Standup.duration_minutes)).filter(
        Standup.duration_minutes.isnot(None)
    ).scalar() or 0
    
    return DashboardStats(
        total_standups=total_standups,
        completed_standups=completed_standups,
        total_issues_discussed=total_issues,
        blocked_issues_count=blocked_count,
        escalations_created=escalations_count,
        average_duration_minutes=float(avg_duration)
    )


@router.get("/upcoming")
async def get_upcoming_standups(
    limit: int = 5,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get upcoming scheduled standups"""
    now = datetime.utcnow()
    
    upcoming = db.query(StandupConfig).filter(
        StandupConfig.status == "scheduled",
        StandupConfig.scheduled_time > now
    ).order_by(StandupConfig.scheduled_time.asc()).limit(limit).all()
    
    return [
        {
            "id": config.id,
            "team_name": config.team_name,
            "scheduled_time": config.scheduled_time.isoformat(),
            "slack_channel": config.slack_channel_name,
            "member_count": len(config.selected_members or [])
        }
        for config in upcoming
    ]


@router.get("/active")
async def get_active_standups(db: Session = Depends(get_db)) -> List[Dict]:
    """Get currently active standups"""
    active = db.query(Standup).filter(
        Standup.status == "in_progress"
    ).all()
    
    result = []
    for standup in active:
        config = db.query(StandupConfig).filter(
            StandupConfig.id == standup.config_id
        ).first()
        
        result.append({
            "id": standup.id,
            "config_id": standup.config_id,
            "team_id": config.team_id if config else "",
            "team_name": config.team_name if config else "Unknown",
            "jitsi_url": standup.jitsi_url,
            "slack_channel_id": config.slack_channel_id if config else "",
            "started_at": standup.started_at.isoformat() if standup.started_at else None,
            "total_issues": standup.total_issues,
            "completed_issues": standup.completed_issues,
            "progress_percent": (standup.completed_issues / standup.total_issues * 100) if standup.total_issues > 0 else 0
        })
    
    return result


@router.get("/history")
async def get_standup_history(
    days: int = 30,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get standup history"""
    since = datetime.utcnow() - timedelta(days=days)
    
    standups = db.query(Standup).filter(
        Standup.status == "completed",
        Standup.completed_at >= since
    ).order_by(Standup.completed_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for standup in standups:
        config = db.query(StandupConfig).filter(
            StandupConfig.id == standup.config_id
        ).first()
        
        # Get issue stats
        updates = db.query(IssueUpdate).filter(
            IssueUpdate.standup_id == standup.id
        ).all()
        
        blocked_count = sum(1 for u in updates if u.status == "blocked")
        escalation_count = sum(1 for u in updates if u.escalation_ticket_id)
        
        result.append({
            "id": standup.id,
            "team_name": config.team_name if config else "Unknown",
            "completed_at": standup.completed_at.isoformat() if standup.completed_at else None,
            "duration_minutes": standup.duration_minutes,
            "total_issues": standup.total_issues,
            "blocked_count": blocked_count,
            "escalation_count": escalation_count
        })
    
    return result


@router.get("/trends/blocked")
async def get_blocked_trend(
    days: int = 30,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get blocked issues trend over time"""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get daily blocked counts
    results = db.query(
        func.date(IssueUpdate.extracted_at).label("date"),
        func.count(IssueUpdate.id).label("total"),
        func.sum(func.cast(IssueUpdate.status == "blocked", Integer)).label("blocked")
    ).filter(
        IssueUpdate.extracted_at >= since
    ).group_by(
        func.date(IssueUpdate.extracted_at)
    ).order_by(
        func.date(IssueUpdate.extracted_at)
    ).all()
    
    return [
        {
            "date": str(r.date),
            "total": r.total,
            "blocked": r.blocked or 0
        }
        for r in results
    ]


@router.get("/trends/escalations")
async def get_escalation_trend(
    days: int = 30,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get escalation trend over time"""
    since = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        func.date(IssueUpdate.extracted_at).label("date"),
        func.count(IssueUpdate.escalation_ticket_id).label("escalations")
    ).filter(
        IssueUpdate.extracted_at >= since,
        IssueUpdate.escalation_ticket_id.isnot(None)
    ).group_by(
        func.date(IssueUpdate.extracted_at)
    ).order_by(
        func.date(IssueUpdate.extracted_at)
    ).all()
    
    return [
        {
            "date": str(r.date),
            "escalations": r.escalations
        }
        for r in results
    ]


# Import Integer for casting
from sqlalchemy import Integer
