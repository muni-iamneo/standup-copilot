"""
Scheduler Service
Handles scheduled standup execution using APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Optional, Callable
import asyncio

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import StandupConfig, Standup
from app.services.jitsi_service import jitsi_service
from app.services.slack_service import slack_service
from app.services.linear_service import linear_service


class SchedulerService:
    """Service for scheduling and executing standups"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            print("Scheduler started")
            
            # Add job to check for pending standups every minute
            self.scheduler.add_job(
                self._check_pending_standups,
                CronTrigger(minute="*"),  # Every minute
                id="check_pending_standups",
                replace_existing=True
            )
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Scheduler stopped")
    
    async def _check_pending_standups(self):
        """Check for standups scheduled to start now"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            # Find standups scheduled within the next minute
            window_start = now
            window_end = now + timedelta(minutes=1)
            
            pending_configs = db.query(StandupConfig).filter(
                StandupConfig.status == "scheduled",
                StandupConfig.scheduled_time >= window_start,
                StandupConfig.scheduled_time < window_end
            ).all()
            
            for config in pending_configs:
                await self._execute_standup(db, config)
                
        except Exception as e:
            print(f"Error checking pending standups: {e}")
        finally:
            db.close()
    
    async def _execute_standup(self, db: Session, config: StandupConfig):
        """Execute a scheduled standup"""
        try:
            print(f"Executing standup for team: {config.team_name}")
            
            # Generate Jitsi URL
            jitsi_url = jitsi_service.generate_meeting_url("standup")
            
            # Create standup record
            standup = Standup(
                config_id=config.id,
                jitsi_url=jitsi_url,
                started_at=datetime.utcnow(),
                status="in_progress"
            )
            db.add(standup)
            
            # Fetch issues from Linear
            if config.auto_fetch_issues:
                issues = await linear_service.get_team_issues(config.team_id, active_only=True)
            else:
                # Fetch specific issues
                issues = []
                for issue_id in config.selected_issue_ids:
                    issue = await linear_service.get_issue(issue_id)
                    if issue:
                        issues.append(issue)
            
            standup.total_issues = len(issues)
            
            # Update config status
            config.status = "in_progress"
            db.commit()
            
            # Send Slack notification
            await slack_service.send_standup_notification(
                channel_id=config.slack_channel_id,
                team_name=config.team_name,
                scheduled_time=config.scheduled_time,
                jitsi_url=jitsi_url,
                participants=config.selected_members,
                issues=issues
            )
            
            print(f"Standup started: {standup.id} - {jitsi_url}")
            
        except Exception as e:
            print(f"Error executing standup: {e}")
            config.status = "failed"
            db.commit()
    
    def schedule_standup(
        self,
        config_id: int,
        scheduled_time: datetime,
        callback: Optional[Callable] = None
    ):
        """Schedule a standup for a specific time"""
        job_id = f"standup_{config_id}"
        
        self.scheduler.add_job(
            self._trigger_standup,
            DateTrigger(run_date=scheduled_time),
            args=[config_id, callback],
            id=job_id,
            replace_existing=True
        )
        
        print(f"Scheduled standup {config_id} for {scheduled_time}")
        return job_id
    
    async def _trigger_standup(self, config_id: int, callback: Optional[Callable] = None):
        """Trigger a specific standup"""
        db = SessionLocal()
        try:
            config = db.query(StandupConfig).filter(
                StandupConfig.id == config_id
            ).first()
            
            if config and config.status == "scheduled":
                await self._execute_standup(db, config)
                
                if callback:
                    callback(config_id)
                    
        except Exception as e:
            print(f"Error triggering standup {config_id}: {e}")
        finally:
            db.close()
    
    def cancel_standup(self, config_id: int) -> bool:
        """Cancel a scheduled standup"""
        job_id = f"standup_{config_id}"
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            print(f"Error canceling standup: {e}")
            return False
    
    def get_scheduled_jobs(self) -> list:
        """Get list of scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return jobs


# Singleton instance
scheduler_service = SchedulerService()
