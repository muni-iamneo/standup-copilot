"""
StandupAI Database Models
SQLAlchemy ORM models for PostgreSQL database
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class StandupConfig(Base):
    """Configuration for scheduled standups"""
    __tablename__ = "standup_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String(255), nullable=False)
    team_name = Column(String(255), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    slack_channel_id = Column(String(255), nullable=False)
    slack_channel_name = Column(String(255), nullable=False)
    selected_members = Column(JSON, default=[])  # Array of {user_id, name, email}
    auto_fetch_issues = Column(Boolean, default=True)
    selected_issue_ids = Column(JSON, default=[])  # Array of specific issue IDs
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
    
    # Relationships
    standups = relationship("Standup", back_populates="config")


class Standup(Base):
    """Individual standup meeting instance"""
    __tablename__ = "standups"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("standup_configs.id"), nullable=False)
    jitsi_url = Column(String(500))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed
    total_issues = Column(Integer, default=0)
    completed_issues = Column(Integer, default=0)
    duration_minutes = Column(Integer)
    
    config = relationship("StandupConfig", back_populates="standups")
    issue_updates = relationship("IssueUpdate", back_populates="standup")
    pm_summary = relationship("PMSummary", back_populates="standup", uselist=False)


class IssueUpdate(Base):
    """Updates extracted from standup for each Linear issue"""
    __tablename__ = "issue_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    standup_id = Column(Integer, ForeignKey("standups.id"), nullable=False)
    linear_issue_id = Column(String(50), nullable=False)  # e.g., "ENG-123"
    linear_issue_key = Column(String(255))  # UUID from Linear
    issue_title = Column(String(500))
    assignee_name = Column(String(255))
    assignee_email = Column(String(255))
    status = Column(String(50))  # progressing, blocked, completed, at_risk
    blockers = Column(Text)
    dependencies = Column(Text)
    eta = Column(String(100))
    next_steps = Column(Text)
    escalation_needed = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    escalation_ticket_id = Column(String(50))  # If escalation created
    transcript = Column(Text)  # Full text of what developer said
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    linear_comment_posted = Column(Boolean, default=False)
    linear_status_updated = Column(Boolean, default=False)
    
    # Relationships
    standup = relationship("Standup", back_populates="issue_updates")


class PMSummary(Base):
    """Summary generated for PM after standup completion"""
    __tablename__ = "pm_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    standup_id = Column(Integer, ForeignKey("standups.id"), nullable=False, unique=True)
    progress_issues = Column(JSON, default=[])  # Array of issue IDs going well
    blocked_issues = Column(JSON, default=[])  # Array of blocked issue IDs
    at_risk_issues = Column(JSON, default=[])  # Array of at-risk issue IDs
    escalations_created = Column(JSON, default=[])  # Array of {old_issue_id, new_escalation_ticket_id}
    slack_sent = Column(Boolean, default=False)
    slack_sent_at = Column(DateTime(timezone=True))
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True))
    summary_text = Column(Text)  # Full formatted summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    standup = relationship("Standup", back_populates="pm_summary")
