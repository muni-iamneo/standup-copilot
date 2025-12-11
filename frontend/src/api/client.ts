import axios from 'axios';
import type {
    StandupConfig,
    Standup,
    IssueUpdate,
    PMSummary,
    DashboardStats,
    UpcomingStandup,
    ActiveStandup,
    StandupHistory,
    LinearTeam,
    LinearIssue,
    SlackChannel,
    TeamMember,
    StandupConfigForm,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ============== Config Endpoints ==============

export const getLinearTeams = async (): Promise<LinearTeam[]> => {
    const response = await api.get('/config/linear/teams');
    return response.data;
};

export const getLinearTeamMembers = async (teamId: string): Promise<TeamMember[]> => {
    const response = await api.get(`/config/linear/teams/${teamId}/members`);
    return response.data;
};

export const getLinearTeamIssues = async (teamId: string, activeOnly = true): Promise<LinearIssue[]> => {
    const response = await api.get(`/config/linear/teams/${teamId}/issues`, {
        params: { active_only: activeOnly },
    });
    return response.data;
};

export const getSlackChannels = async (): Promise<SlackChannel[]> => {
    const response = await api.get('/config/slack/channels');
    return response.data;
};

export const getSlackUsers = async (): Promise<TeamMember[]> => {
    const response = await api.get('/config/slack/users');
    return response.data;
};

export const checkIntegrationHealth = async (): Promise<{ linear: boolean; slack: boolean; elevenlabs: boolean; jitsi: boolean }> => {
    const response = await api.get('/config/health');
    return response.data;
};

// ============== Standup Config Endpoints ==============

export const createStandupConfig = async (config: StandupConfigForm): Promise<StandupConfig> => {
    // Transform members to use user_id instead of id
    const transformedConfig = {
        ...config,
        selected_members: config.selected_members.map((member: any) => ({
            user_id: member.user_id || member.id,
            name: member.name,
            email: member.email,
            avatar_url: member.avatar_url || member.avatarUrl,
        })),
    };
    const response = await api.post('/standups/configs', transformedConfig);
    return response.data;
};

export const getStandupConfigs = async (status?: string): Promise<StandupConfig[]> => {
    const response = await api.get('/standups/configs', {
        params: { status },
    });
    return response.data;
};

export const getStandupConfig = async (configId: number): Promise<StandupConfig> => {
    const response = await api.get(`/standups/configs/${configId}`);
    return response.data;
};

export const updateStandupConfig = async (
    configId: number,
    updates: Partial<StandupConfigForm>
): Promise<StandupConfig> => {
    const response = await api.put(`/standups/configs/${configId}`, updates);
    return response.data;
};

export const deleteStandupConfig = async (configId: number): Promise<void> => {
    await api.delete(`/standups/configs/${configId}`);
};

// ============== Standup Endpoints ==============

export const startStandup = async (configId: number): Promise<Standup> => {
    const response = await api.post(`/standups/start/${configId}`);
    return response.data;
};

export const getStandup = async (standupId: number): Promise<Standup> => {
    const response = await api.get(`/standups/${standupId}`);
    return response.data;
};

export const getStandups = async (status?: string): Promise<Standup[]> => {
    const response = await api.get('/standups/', {
        params: { status },
    });
    return response.data;
};

export const completeStandup = async (standupId: number): Promise<Standup> => {
    const response = await api.post(`/standups/${standupId}/complete`);
    return response.data;
};

// ============== Issue Update Endpoints ==============

export const getIssueUpdates = async (standupId: number): Promise<IssueUpdate[]> => {
    const response = await api.get(`/standups/${standupId}/updates`);
    return response.data;
};

export const processTranscript = async (
    standupId: number,
    data: { transcript: string; issue_id: string; issue_title: string; assignee_name: string }
): Promise<IssueUpdate> => {
    const response = await api.post(`/standups/${standupId}/process-transcript`, data);
    return response.data;
};

// ============== PM Summary Endpoints ==============

export const generatePMSummary = async (standupId: number): Promise<PMSummary> => {
    const response = await api.post(`/standups/${standupId}/summary`);
    return response.data;
};

export const getPMSummary = async (standupId: number): Promise<PMSummary> => {
    const response = await api.get(`/standups/${standupId}/summary`);
    return response.data;
};

// ============== Analytics Endpoints ==============

export const getDashboardStats = async (): Promise<DashboardStats> => {
    const response = await api.get('/analytics/dashboard');
    return response.data;
};

export const getUpcomingStandups = async (limit = 5): Promise<UpcomingStandup[]> => {
    const response = await api.get('/analytics/upcoming', {
        params: { limit },
    });
    return response.data;
};

export const getActiveStandups = async (): Promise<ActiveStandup[]> => {
    const response = await api.get('/analytics/active');
    return response.data;
};

export const getStandupHistory = async (days = 30, skip = 0, limit = 20): Promise<StandupHistory[]> => {
    const response = await api.get('/analytics/history', {
        params: { days, skip, limit },
    });
    return response.data;
};

export const getBlockedTrend = async (days = 30) => {
    const response = await api.get('/analytics/trends/blocked', {
        params: { days },
    });
    return response.data;
};

export const getEscalationTrend = async (days = 30) => {
    const response = await api.get('/analytics/trends/escalations', {
        params: { days },
    });
    return response.data;
};

export default api;
