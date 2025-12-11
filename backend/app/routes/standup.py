"""
Standup Routes
API endpoints for standup management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import StandupConfig, Standup, IssueUpdate, PMSummary
from app.schemas import (
    StandupConfigCreate, StandupConfigUpdate, StandupConfigResponse,
    StandupCreate, StandupResponse, IssueUpdateCreate, IssueUpdateResponse,
    PMSummaryCreate, PMSummaryResponse, ExtractedUpdate, TranscriptInput
)
from app.services.jitsi_service import jitsi_service
from app.services.linear_service import linear_service
from app.services.slack_service import slack_service
from app.services.reasoning_service import reasoning_service
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/standups", tags=["Standups"])


# ============== Standup Config Endpoints ==============

@router.post("/configs", response_model=StandupConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_standup_config(
    config: StandupConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new standup configuration and send Jitsi meeting link to Slack"""
    import logging
    logger = logging.getLogger("standup.create")
    
    logger.info(f"[CREATE] Creating standup config for team: {config.team_name}")
    
    # Generate Jitsi meeting URL immediately
    jitsi_url = jitsi_service.generate_meeting_url("standup")
    logger.info(f"[CREATE] Generated Jitsi URL: {jitsi_url}")
    
    db_config = StandupConfig(
        team_id=config.team_id,
        team_name=config.team_name,
        scheduled_time=config.scheduled_time,
        slack_channel_id=config.slack_channel_id,
        slack_channel_name=config.slack_channel_name,
        selected_members=[m.dict() for m in config.selected_members],
        auto_fetch_issues=config.auto_fetch_issues,
        selected_issue_ids=config.selected_issue_ids or [],
        status="scheduled",
        created_by=config.created_by or "system"
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    logger.info(f"[CREATE] Created config with ID: {db_config.id}")
    
    # Create Standup record immediately so we have an ID for the meeting URL
    standup = Standup(
        config_id=db_config.id,
        jitsi_url=jitsi_url,
        status="scheduled"
    )
    db.add(standup)
    db.commit()
    db.refresh(standup)
    logger.info(f"[CREATE] Created standup with ID: {standup.id}")
    
    # Fetch issues for the notification
    if config.auto_fetch_issues:
        try:
            issues = await linear_service.get_team_issues(config.team_id, active_only=True)
            logger.info(f"[CREATE] Fetched {len(issues)} issues from Linear")
        except Exception as e:
            logger.error(f"[CREATE] Error fetching issues: {e}")
            issues = []
    else:
        issues = []
        for issue_id in (config.selected_issue_ids or []):
            try:
                issue = await linear_service.get_issue(issue_id)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.error(f"[CREATE] Error fetching issue {issue_id}: {e}")
    
    # Update standup with issue count
    standup.total_issues = len(issues)
    db.commit()
    
    # Build frontend meeting URL (this is what users should click)
    # Format: http://localhost:5173/meeting/{standup_id}?jitsi=...&team_id=...&slack_channel_id=...
    from urllib.parse import quote
    frontend_base = "http://localhost:5173"  # TODO: Make configurable
    room_name = jitsi_url.split("/")[-1] if jitsi_url else ""
    
    frontend_meeting_url = (
        f"{frontend_base}/meeting/{standup.id}"
        f"?jitsi={quote(jitsi_url)}"
        f"&room={quote(room_name)}"
        f"&team_id={quote(config.team_id)}"
        f"&slack_channel_id={quote(config.slack_channel_id)}"
    )
    logger.info(f"[CREATE] Frontend meeting URL: {frontend_meeting_url}")
    
    # Send Slack notification with FRONTEND meeting link (not raw Jitsi)
    try:
        await slack_service.send_standup_notification(
            channel_id=config.slack_channel_id,
            team_name=config.team_name,
            scheduled_time=config.scheduled_time,
            jitsi_url=frontend_meeting_url,  # Send frontend URL, not raw Jitsi
            participants=[m.dict() for m in config.selected_members],
            issues=issues
        )
        logger.info(f"[CREATE] Sent Slack notification to channel: {config.slack_channel_id}")
    except Exception as e:
        logger.error(f"[CREATE] Error sending Slack notification: {e}")
    
    # Schedule the standup for automated execution
    scheduler_service.schedule_standup(
        config_id=db_config.id,
        scheduled_time=config.scheduled_time
    )
    logger.info(f"[CREATE] Scheduled standup for: {config.scheduled_time}")
    
    return db_config


@router.get("/configs", response_model=List[StandupConfigResponse])
async def get_standup_configs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all standup configurations"""
    query = db.query(StandupConfig)
    
    if status:
        query = query.filter(StandupConfig.status == status)
    
    configs = query.order_by(StandupConfig.scheduled_time.desc()).offset(skip).limit(limit).all()
    return configs


@router.get("/configs/{config_id}", response_model=StandupConfigResponse)
async def get_standup_config(config_id: int, db: Session = Depends(get_db)):
    """Get a specific standup configuration"""
    config = db.query(StandupConfig).filter(StandupConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.put("/configs/{config_id}", response_model=StandupConfigResponse)
async def update_standup_config(
    config_id: int,
    updates: StandupConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a standup configuration"""
    config = db.query(StandupConfig).filter(StandupConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "selected_members" and value:
            value = [m.dict() if hasattr(m, 'dict') else m for m in value]
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    # Reschedule if time changed
    if updates.scheduled_time:
        scheduler_service.cancel_standup(config_id)
        scheduler_service.schedule_standup(config_id, updates.scheduled_time)
    
    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_standup_config(config_id: int, db: Session = Depends(get_db)):
    """Delete a standup configuration"""
    config = db.query(StandupConfig).filter(StandupConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    scheduler_service.cancel_standup(config_id)
    db.delete(config)
    db.commit()


# ============== Standup Execution Endpoints ==============

@router.post("/start/{config_id}", response_model=StandupResponse)
async def start_standup(config_id: int, db: Session = Depends(get_db)):
    """Manually start a standup"""
    config = db.query(StandupConfig).filter(StandupConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Generate Jitsi URL
    jitsi_url = jitsi_service.generate_meeting_url("standup")
    
    # Create standup record
    standup = Standup(
        config_id=config_id,
        jitsi_url=jitsi_url,
        started_at=datetime.utcnow(),
        status="in_progress"
    )
    
    # Fetch issues
    if config.auto_fetch_issues:
        issues = await linear_service.get_team_issues(config.team_id, active_only=True)
    else:
        issues = []
        for issue_id in config.selected_issue_ids:
            issue = await linear_service.get_issue(issue_id)
            if issue:
                issues.append(issue)
    
    standup.total_issues = len(issues)
    
    db.add(standup)
    config.status = "in_progress"
    db.commit()
    db.refresh(standup)
    
    # Send Slack notification
    await slack_service.send_standup_notification(
        channel_id=config.slack_channel_id,
        team_name=config.team_name,
        scheduled_time=config.scheduled_time,
        jitsi_url=jitsi_url,
        participants=config.selected_members,
        issues=issues
    )
    
    return standup


@router.get("/{standup_id}", response_model=StandupResponse)
async def get_standup(standup_id: int, db: Session = Depends(get_db)):
    """Get a specific standup"""
    standup = db.query(Standup).filter(Standup.id == standup_id).first()
    if not standup:
        raise HTTPException(status_code=404, detail="Standup not found")
    return standup


@router.get("/", response_model=List[StandupResponse])
async def get_standups(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all standups"""
    query = db.query(Standup)
    
    if status:
        query = query.filter(Standup.status == status)
    
    standups = query.order_by(Standup.started_at.desc()).offset(skip).limit(limit).all()
    return standups


@router.post("/{standup_id}/complete", response_model=StandupResponse)
async def complete_standup(standup_id: int, db: Session = Depends(get_db)):
    """Mark a standup as complete"""
    standup = db.query(Standup).filter(Standup.id == standup_id).first()
    if not standup:
        raise HTTPException(status_code=404, detail="Standup not found")
    
    standup.status = "completed"
    standup.completed_at = datetime.utcnow()
    
    if standup.started_at:
        duration = (standup.completed_at - standup.started_at).total_seconds() / 60
        standup.duration_minutes = int(duration)
    
    # Update config status
    config = db.query(StandupConfig).filter(StandupConfig.id == standup.config_id).first()
    if config:
        config.status = "completed"
    
    db.commit()
    db.refresh(standup)
    
    return standup


# ============== Issue Update Endpoints ==============

@router.post("/{standup_id}/updates", response_model=IssueUpdateResponse)
async def create_issue_update(
    standup_id: int,
    update: IssueUpdateCreate,
    db: Session = Depends(get_db)
):
    """Create an issue update from transcript"""
    standup = db.query(Standup).filter(Standup.id == standup_id).first()
    if not standup:
        raise HTTPException(status_code=404, detail="Standup not found")
    
    db_update = IssueUpdate(
        standup_id=standup_id,
        linear_issue_id=update.linear_issue_id,
        linear_issue_key=update.linear_issue_key,
        issue_title=update.issue_title,
        assignee_name=update.assignee_name,
        assignee_email=update.assignee_email,
        status=update.status,
        blockers=update.blockers,
        dependencies=update.dependencies,
        eta=update.eta,
        next_steps=update.next_steps,
        escalation_needed=update.escalation_needed,
        escalation_reason=update.escalation_reason,
        transcript=update.transcript
    )
    
    db.add(db_update)
    standup.completed_issues = standup.completed_issues + 1
    db.commit()
    db.refresh(db_update)
    
    return db_update


@router.post("/{standup_id}/process-transcript", response_model=IssueUpdateResponse)
async def process_transcript(
    standup_id: int,
    input_data: TranscriptInput,
    db: Session = Depends(get_db)
):
    """Process transcript using LLM and create issue update"""
    standup = db.query(Standup).filter(Standup.id == standup_id).first()
    if not standup:
        raise HTTPException(status_code=404, detail="Standup not found")
    
    # Extract structured data from transcript
    extracted = await reasoning_service.extract_update_from_transcript(
        transcript=input_data.transcript,
        issue_id=input_data.issue_id,
        issue_title=input_data.issue_title,
        assignee_name=input_data.assignee_name
    )
    
    # Create issue update
    db_update = IssueUpdate(
        standup_id=standup_id,
        linear_issue_id=input_data.issue_id,
        issue_title=input_data.issue_title,
        assignee_name=input_data.assignee_name,
        status=extracted.get("status", "progressing"),
        blockers=extracted.get("blockers"),
        dependencies=extracted.get("dependencies"),
        eta=extracted.get("eta"),
        next_steps=extracted.get("next_steps"),
        escalation_needed=extracted.get("escalation_needed", False),
        escalation_reason=extracted.get("escalation_reason"),
        transcript=input_data.transcript
    )
    
    db.add(db_update)
    standup.completed_issues = standup.completed_issues + 1
    
    # Post comment to Linear
    comment = await reasoning_service.generate_linear_comment(
        status=db_update.status,
        blockers=db_update.blockers,
        dependencies=db_update.dependencies,
        eta=db_update.eta,
        next_steps=db_update.next_steps,
        escalation_needed=db_update.escalation_needed,
        escalation_reason=db_update.escalation_reason
    )
    
    if db_update.linear_issue_key:
        await linear_service.add_comment(db_update.linear_issue_key, comment)
        db_update.linear_comment_posted = True
    
    # Create escalation if needed
    if db_update.escalation_needed:
        config = db.query(StandupConfig).filter(StandupConfig.id == standup.config_id).first()
        if config:
            escalation = await linear_service.create_escalation_issue(
                team_id=config.team_id,
                title=f"[ESCALATION] Unblock {input_data.issue_id}: {input_data.issue_title}",
                description=f"{db_update.assignee_name}'s work on {input_data.issue_id} is blocked. {db_update.escalation_reason}",
                parent_issue_id=db_update.linear_issue_key,
                priority=1
            )
            if escalation.get("success"):
                db_update.escalation_ticket_id = escalation.get("issue", {}).get("identifier")
    
    db.commit()
    db.refresh(db_update)
    
    return db_update


@router.get("/{standup_id}/updates", response_model=List[IssueUpdateResponse])
async def get_issue_updates(standup_id: int, db: Session = Depends(get_db)):
    """Get all issue updates for a standup"""
    updates = db.query(IssueUpdate).filter(IssueUpdate.standup_id == standup_id).all()
    return updates


# ============== PM Summary Endpoints ==============

@router.post("/{standup_id}/summary", response_model=PMSummaryResponse)
async def generate_pm_summary(standup_id: int, db: Session = Depends(get_db)):
    """Generate and send PM summary"""
    standup = db.query(Standup).filter(Standup.id == standup_id).first()
    if not standup:
        raise HTTPException(status_code=404, detail="Standup not found")
    
    updates = db.query(IssueUpdate).filter(IssueUpdate.standup_id == standup_id).all()
    
    # Categorize issues
    progress_issues = [u.linear_issue_id for u in updates if u.status == "progressing"]
    blocked_issues = [u.linear_issue_id for u in updates if u.status == "blocked"]
    at_risk_issues = [u.linear_issue_id for u in updates if u.status == "at_risk"]
    escalations = [
        {"old_issue_id": u.linear_issue_id, "new_escalation_ticket_id": u.escalation_ticket_id}
        for u in updates if u.escalation_ticket_id
    ]
    
    # Generate summary text
    config = db.query(StandupConfig).filter(StandupConfig.id == standup.config_id).first()
    team_name = config.team_name if config else "Unknown Team"
    
    summary_text = await reasoning_service.generate_standup_summary(
        [{"issue_id": u.linear_issue_id, "issue_title": u.issue_title, "status": u.status, "blockers": u.blockers, "eta": u.eta} for u in updates],
        team_name
    )
    
    # Create PM summary
    pm_summary = PMSummary(
        standup_id=standup_id,
        progress_issues=progress_issues,
        blocked_issues=blocked_issues,
        at_risk_issues=at_risk_issues,
        escalations_created=escalations,
        summary_text=summary_text
    )
    
    db.add(pm_summary)
    db.commit()
    db.refresh(pm_summary)
    
    return pm_summary


@router.get("/{standup_id}/summary", response_model=PMSummaryResponse)
async def get_pm_summary(standup_id: int, db: Session = Depends(get_db)):
    """Get PM summary for a standup"""
    summary = db.query(PMSummary).filter(PMSummary.standup_id == standup_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary
