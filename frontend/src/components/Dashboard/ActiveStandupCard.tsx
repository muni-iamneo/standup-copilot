import { Video, ExternalLink, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { ActiveStandup } from '../../types';

interface Props {
    standup: ActiveStandup;
}

export default function ActiveStandupCard({ standup }: Props) {
    // Build meeting URL with Jitsi details and config as query params
    const meetingUrl = `/meeting/${standup.id}?jitsi=${encodeURIComponent(standup.jitsi_url)}&room=${encodeURIComponent(standup.jitsi_url.split('/').pop() || '')}&team_id=${encodeURIComponent(standup.team_id || '')}&slack_channel_id=${encodeURIComponent(standup.slack_channel_id || '')}`;

    return (
        <div className="p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 group">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <div className="pulse-dot" />
                    <h4 className="font-semibold text-white">{standup.team_name}</h4>
                </div>
                <div className="flex items-center gap-2">
                    {/* Join with AI Agent */}
                    <Link
                        to={meetingUrl}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-500 text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors"
                    >
                        <Bot className="w-4 h-4" />
                        Join with AI
                    </Link>
                    {/* Direct Jitsi link */}
                    <a
                        href={standup.jitsi_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 px-2 py-1.5 bg-white/10 text-white/70 text-sm rounded-lg hover:bg-white/20 transition-colors"
                        title="Open in new tab"
                    >
                        <Video className="w-4 h-4" />
                        <ExternalLink className="w-3 h-3" />
                    </a>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-2">
                <div className="flex items-center justify-between text-xs text-white/60 mb-1">
                    <span>Progress</span>
                    <span>{standup.completed_issues}/{standup.total_issues} issues</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${standup.progress_percent}%` }}
                    />
                </div>
            </div>

            <div className="flex items-center justify-between text-xs text-white/50">
                <span>Started {new Date(standup.started_at).toLocaleTimeString()}</span>
                <Link
                    to={`/standup/${standup.id}`}
                    className="text-primary-400 hover:text-primary-300"
                >
                    View Details →
                </Link>
            </div>
        </div>
    );
}

