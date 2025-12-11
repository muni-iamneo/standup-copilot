import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    ArrowLeft,
    Video,
    Clock,
    Users,
    CheckCircle,
    XCircle,
    AlertTriangle,
    TrendingUp,
    ExternalLink,
    MessageSquare,
} from 'lucide-react';
import { getStandup, getIssueUpdates, getPMSummary } from '../api/client';
import type { Standup, IssueUpdate, PMSummary } from '../types';
import LoadingSpinner from '../components/Common/LoadingSpinner';

export default function StandupDetailPage() {
    const { id } = useParams<{ id: string }>();
    const [standup, setStandup] = useState<Standup | null>(null);
    const [updates, setUpdates] = useState<IssueUpdate[]>([]);
    const [summary, setSummary] = useState<PMSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'issues' | 'summary'>('issues');

    useEffect(() => {
        if (!id) return;

        Promise.all([
            getStandup(parseInt(id)),
            getIssueUpdates(parseInt(id)),
            getPMSummary(parseInt(id)).catch(() => null),
        ])
            .then(([standupData, updatesData, summaryData]) => {
                setStandup(standupData);
                setUpdates(updatesData);
                setSummary(summaryData);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <LoadingSpinner size="lg" text="Loading standup details..." />
            </div>
        );
    }

    if (!standup) {
        return (
            <div className="text-center py-16">
                <p className="text-white/60">Standup not found</p>
                <Link to="/history" className="text-primary-400 hover:text-primary-300 mt-4 inline-block">
                    ← Back to History
                </Link>
            </div>
        );
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'progressing':
                return <TrendingUp className="w-4 h-4 text-green-400" />;
            case 'blocked':
                return <XCircle className="w-4 h-4 text-red-400" />;
            case 'completed':
                return <CheckCircle className="w-4 h-4 text-blue-400" />;
            case 'at_risk':
                return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
            default:
                return null;
        }
    };

    const getStatusClass = (status: string) => {
        switch (status) {
            case 'progressing':
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'blocked':
                return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'completed':
                return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'at_risk':
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            default:
                return 'bg-white/10 text-white/60';
        }
    };

    return (
        <div className="max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <Link
                    to="/history"
                    className="inline-flex items-center gap-2 text-white/60 hover:text-white mb-4"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to History
                </Link>

                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            {standup.config?.team_name || 'Standup'} Details
                        </h1>
                        <div className="flex items-center gap-4 text-white/60">
                            <div className="flex items-center gap-1.5">
                                <Clock className="w-4 h-4" />
                                {standup.started_at
                                    ? new Date(standup.started_at).toLocaleString()
                                    : 'Not started'}
                            </div>
                            {standup.duration_minutes && (
                                <span>• {standup.duration_minutes} minutes</span>
                            )}
                            <span
                                className={`px-2 py-1 text-xs font-medium rounded-full ${standup.status === 'completed'
                                        ? 'bg-green-500/20 text-green-400'
                                        : standup.status === 'in_progress'
                                            ? 'bg-blue-500/20 text-blue-400'
                                            : 'bg-white/10 text-white/60'
                                    }`}
                            >
                                {standup.status}
                            </span>
                        </div>
                    </div>

                    {standup.jitsi_url && (
                        <a
                            href={standup.jitsi_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-secondary flex items-center gap-2"
                        >
                            <Video className="w-4 h-4" />
                            View Recording
                            <ExternalLink className="w-3 h-3" />
                        </a>
                    )}
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="card text-center">
                    <p className="text-3xl font-bold text-white">{standup.total_issues}</p>
                    <p className="text-sm text-white/50">Total Issues</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-green-400">
                        {updates.filter((u) => u.status === 'progressing').length}
                    </p>
                    <p className="text-sm text-white/50">Progressing</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-red-400">
                        {updates.filter((u) => u.status === 'blocked').length}
                    </p>
                    <p className="text-sm text-white/50">Blocked</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-yellow-400">
                        {updates.filter((u) => u.escalation_needed).length}
                    </p>
                    <p className="text-sm text-white/50">Escalations</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                <button
                    onClick={() => setActiveTab('issues')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'issues'
                            ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                            : 'text-white/60 hover:text-white hover:bg-white/5'
                        }`}
                >
                    Issue Updates ({updates.length})
                </button>
                <button
                    onClick={() => setActiveTab('summary')}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'summary'
                            ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                            : 'text-white/60 hover:text-white hover:bg-white/5'
                        }`}
                >
                    PM Summary
                </button>
            </div>

            {/* Content */}
            {activeTab === 'issues' ? (
                <div className="space-y-4">
                    {updates.map((update) => (
                        <div key={update.id} className="card">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-mono text-primary-400">
                                            {update.linear_issue_id}
                                        </span>
                                        <span
                                            className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getStatusClass(
                                                update.status
                                            )}`}
                                        >
                                            <span className="flex items-center gap-1">
                                                {getStatusIcon(update.status)}
                                                {update.status}
                                            </span>
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-semibold text-white">
                                        {update.issue_title}
                                    </h3>
                                    <p className="text-sm text-white/50">
                                        Assigned to {update.assignee_name || 'Unassigned'}
                                    </p>
                                </div>
                                {update.linear_comment_posted && (
                                    <span className="flex items-center gap-1 text-xs text-green-400">
                                        <MessageSquare className="w-3 h-3" />
                                        Posted to Linear
                                    </span>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                {update.blockers && (
                                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <p className="text-red-400 font-medium mb-1">Blockers</p>
                                        <p className="text-white/70">{update.blockers}</p>
                                    </div>
                                )}
                                {update.dependencies && (
                                    <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                                        <p className="text-yellow-400 font-medium mb-1">Dependencies</p>
                                        <p className="text-white/70">{update.dependencies}</p>
                                    </div>
                                )}
                                {update.next_steps && (
                                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                        <p className="text-blue-400 font-medium mb-1">Next Steps</p>
                                        <p className="text-white/70">{update.next_steps}</p>
                                    </div>
                                )}
                                {update.eta && (
                                    <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                                        <p className="text-green-400 font-medium mb-1">ETA</p>
                                        <p className="text-white/70">{update.eta}</p>
                                    </div>
                                )}
                            </div>

                            {update.escalation_needed && (
                                <div className="mt-4 p-3 rounded-lg bg-orange-500/10 border border-orange-500/30">
                                    <div className="flex items-center gap-2 text-orange-400 font-medium mb-1">
                                        <AlertTriangle className="w-4 h-4" />
                                        Escalation Created
                                    </div>
                                    <p className="text-white/70 text-sm">{update.escalation_reason}</p>
                                    {update.escalation_ticket_id && (
                                        <p className="text-xs text-orange-400 mt-1">
                                            Ticket: {update.escalation_ticket_id}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card">
                    {summary ? (
                        <div className="space-y-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
                                    <p className="text-2xl font-bold text-green-400">
                                        {summary.progress_issues.length}
                                    </p>
                                    <p className="text-sm text-white/50">Progressing</p>
                                </div>
                                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                                    <p className="text-2xl font-bold text-red-400">
                                        {summary.blocked_issues.length}
                                    </p>
                                    <p className="text-sm text-white/50">Blocked</p>
                                </div>
                                <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-center">
                                    <p className="text-2xl font-bold text-yellow-400">
                                        {summary.at_risk_issues.length}
                                    </p>
                                    <p className="text-sm text-white/50">At Risk</p>
                                </div>
                                <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20 text-center">
                                    <p className="text-2xl font-bold text-orange-400">
                                        {summary.escalations_created.length}
                                    </p>
                                    <p className="text-sm text-white/50">Escalations</p>
                                </div>
                            </div>

                            {summary.summary_text && (
                                <div>
                                    <h4 className="font-semibold text-white mb-3">Summary</h4>
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <p className="text-white/80 whitespace-pre-wrap">{summary.summary_text}</p>
                                    </div>
                                </div>
                            )}

                            <div className="flex items-center gap-4 text-sm text-white/50">
                                {summary.slack_sent && (
                                    <span className="flex items-center gap-1 text-green-400">
                                        <CheckCircle className="w-4 h-4" />
                                        Sent to Slack
                                    </span>
                                )}
                                {summary.email_sent && (
                                    <span className="flex items-center gap-1 text-green-400">
                                        <CheckCircle className="w-4 h-4" />
                                        Email Sent
                                    </span>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-white/50">
                            <p>No summary generated yet</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
