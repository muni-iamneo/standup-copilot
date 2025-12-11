// TypeScript interfaces for StandupAI

export interface TeamMember {
    user_id: string;
    name: string;
    email?: string;
    avatar_url?: string;
    slack_id?: string;
}

export interface LinearTeam {
    id: string;
    name: string;
    key: string;
    description?: string;
}

export interface LinearIssue {
    id: string;
    identifier: string;
    title: string;
    description?: string;
    status?: string;
    priority?: number;
    assignee?: TeamMember;
    state?: {
        id: string;
        name: string;
        type: string;
    };
    created_at?: string;
    updated_at?: string;
}

export interface SlackChannel {
    id: string;
    name: string;
    is_private: boolean;
}

export interface StandupConfig {
    id: number;
    team_id: string;
    team_name: string;
    scheduled_time: string;
    slack_channel_id: string;
    slack_channel_name: string;
    selected_members: TeamMember[];
    auto_fetch_issues: boolean;
    selected_issue_ids: string[];
    status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
    created_at: string;
    created_by?: string;
}

export interface Standup {
    id: number;
    config_id: number;
    jitsi_url?: string;
    started_at?: string;
    completed_at?: string;
    status: 'scheduled' | 'in_progress' | 'completed';
    total_issues: number;
    completed_issues: number;
    duration_minutes?: number;
    config?: StandupConfig;
}

export interface IssueUpdate {
    id: number;
    standup_id: number;
    linear_issue_id: string;
    linear_issue_key?: string;
    issue_title: string;
    assignee_name?: string;
    assignee_email?: string;
    status: 'progressing' | 'blocked' | 'completed' | 'at_risk';
    blockers?: string;
    dependencies?: string;
    eta?: string;
    next_steps?: string;
    escalation_needed: boolean;
    escalation_reason?: string;
    escalation_ticket_id?: string;
    transcript?: string;
    extracted_at: string;
    linear_comment_posted: boolean;
    linear_status_updated: boolean;
}

export interface PMSummary {
    id: number;
    standup_id: number;
    progress_issues: string[];
    blocked_issues: string[];
    at_risk_issues: string[];
    escalations_created: EscalationInfo[];
    slack_sent: boolean;
    slack_sent_at?: string;
    email_sent: boolean;
    email_sent_at?: string;
    summary_text?: string;
    created_at: string;
}

export interface EscalationInfo {
    old_issue_id: string;
    new_escalation_ticket_id: string;
}

export interface DashboardStats {
    total_standups: number;
    completed_standups: number;
    total_issues_discussed: number;
    blocked_issues_count: number;
    escalations_created: number;
    average_duration_minutes: number;
}

export interface UpcomingStandup {
    id: number;
    team_name: string;
    scheduled_time: string;
    slack_channel: string;
    member_count: number;
}

export interface ActiveStandup {
    id: number;
    config_id: number;
    team_id: string;
    team_name: string;
    jitsi_url: string;
    slack_channel_id: string;
    started_at: string;
    total_issues: number;
    completed_issues: number;
    progress_percent: number;
}

export interface StandupHistory {
    id: number;
    team_name: string;
    completed_at: string;
    duration_minutes?: number;
    total_issues: number;
    blocked_count: number;
    escalation_count: number;
}

export interface TrendData {
    date: string;
    total: number;
    blocked: number;
}

export interface EscalationTrend {
    date: string;
    escalations: number;
}

// API Response types
export interface ApiResponse<T> {
    data: T;
    error?: string;
}

// Form types
export interface StandupConfigForm {
    team_id: string;
    team_name: string;
    scheduled_time: string;
    slack_channel_id: string;
    slack_channel_name: string;
    selected_members: TeamMember[];
    auto_fetch_issues: boolean;
    selected_issue_ids: string[];
}
