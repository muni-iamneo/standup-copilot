"""
StandupAI Pydantic Schemas
Request/Response models for API validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ============== Team Member Schemas ==============

class TeamMember(BaseModel):
    """Team member information"""
    user_id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


# ============== Linear Issue Schemas ==============

class LinearIssue(BaseModel):
    """Linear issue information"""
    id: str
    identifier: str  # e.g., "ENG-123"
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    assignee: Optional[TeamMember] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LinearTeam(BaseModel):
    """Linear team information"""
    id: str
    name: str
    key: str
    description: Optional[str] = None


# ============== Slack Schemas ==============

class SlackChannel(BaseModel):
    """Slack channel information"""
    id: str
    name: str
    is_private: bool = False


# ============== Standup Config Schemas ==============

class StandupConfigCreate(BaseModel):
    """Request schema for creating standup configuration"""
    team_id: str
    team_name: str
    scheduled_time: datetime
    slack_channel_id: str
    slack_channel_name: str
    selected_members: List[TeamMember]
    auto_fetch_issues: bool = True
    selected_issue_ids: Optional[List[str]] = []
    created_by: Optional[str] = None


class StandupConfigUpdate(BaseModel):
    """Request schema for updating standup configuration"""
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None
    selected_members: Optional[List[TeamMember]] = None
    auto_fetch_issues: Optional[bool] = None
    selected_issue_ids: Optional[List[str]] = None
    status: Optional[str] = None


class StandupConfigResponse(BaseModel):
    """Response schema for standup configuration"""
    id: int
    team_id: str
    team_name: str
    scheduled_time: datetime
    slack_channel_id: str
    slack_channel_name: str
    selected_members: List[dict]
    auto_fetch_issues: bool
    selected_issue_ids: List[str]
    status: str
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


# ============== Standup Schemas ==============

class StandupCreate(BaseModel):
    """Request schema for creating a standup"""
    config_id: int


class StandupResponse(BaseModel):
    """Response schema for standup"""
    id: int
    config_id: int
    jitsi_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    total_issues: int
    completed_issues: int
    duration_minutes: Optional[int]
    config: Optional[StandupConfigResponse] = None

    class Config:
        from_attributes = True


# ============== Issue Update Schemas ==============

class IssueUpdateCreate(BaseModel):
    """Request schema for creating an issue update"""
    standup_id: int
    linear_issue_id: str
    linear_issue_key: Optional[str] = None
    issue_title: str
    assignee_name: Optional[str] = None
    assignee_email: Optional[str] = None
    status: str  # progressing, blocked, completed, at_risk
    blockers: Optional[str] = None
    dependencies: Optional[str] = None
    eta: Optional[str] = None
    next_steps: Optional[str] = None
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    transcript: Optional[str] = None


class IssueUpdateResponse(BaseModel):
    """Response schema for issue update"""
    id: int
    standup_id: int
    linear_issue_id: str
    linear_issue_key: Optional[str]
    issue_title: str
    assignee_name: Optional[str]
    assignee_email: Optional[str]
    status: str
    blockers: Optional[str]
    dependencies: Optional[str]
    eta: Optional[str]
    next_steps: Optional[str]
    escalation_needed: bool
    escalation_reason: Optional[str]
    escalation_ticket_id: Optional[str]
    transcript: Optional[str]
    extracted_at: datetime
    linear_comment_posted: bool
    linear_status_updated: bool

    class Config:
        from_attributes = True


# ============== PM Summary Schemas ==============

class PMSummaryCreate(BaseModel):
    """Request schema for creating PM summary"""
    standup_id: int
    progress_issues: List[str] = []
    blocked_issues: List[str] = []
    at_risk_issues: List[str] = []
    escalations_created: List[dict] = []
    summary_text: Optional[str] = None


class PMSummaryResponse(BaseModel):
    """Response schema for PM summary"""
    id: int
    standup_id: int
    progress_issues: List[str]
    blocked_issues: List[str]
    at_risk_issues: List[str]
    escalations_created: List[dict]
    slack_sent: bool
    slack_sent_at: Optional[datetime]
    email_sent: bool
    email_sent_at: Optional[datetime]
    summary_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Analytics Schemas ==============

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_standups: int
    completed_standups: int
    total_issues_discussed: int
    blocked_issues_count: int
    escalations_created: int
    average_duration_minutes: float


class StandupAnalytics(BaseModel):
    """Analytics for standup history"""
    date: datetime
    team_name: str
    issues_count: int
    blocked_count: int
    completed_count: int
    duration_minutes: Optional[int]


# ============== AI Processing Schemas ==============

class ExtractedUpdate(BaseModel):
    """Extracted information from developer's verbal update"""
    status: str  # progressing, blocked, completed, at_risk
    blockers: Optional[str] = None
    dependencies: Optional[str] = None
    eta: Optional[str] = None
    next_steps: Optional[str] = None
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None


class TranscriptInput(BaseModel):
    """Input for processing developer transcript"""
    transcript: str
    issue_id: str
    issue_title: str
    assignee_name: str
