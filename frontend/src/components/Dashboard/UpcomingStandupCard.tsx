import { Calendar, Clock, Users, Hash } from 'lucide-react';
import type { UpcomingStandup } from '../../types';

interface Props {
    standup: UpcomingStandup;
}

export default function UpcomingStandupCard({ standup }: Props) {
    const scheduledDate = new Date(standup.scheduled_time);
    const isToday = new Date().toDateString() === scheduledDate.toDateString();

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        });
    };

    const formatDate = (date: Date) => {
        if (isToday) return 'Today';
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/8 hover:border-white/20 transition-all group">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h4 className="font-semibold text-white group-hover:text-primary-300 transition-colors">
                        {standup.team_name}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                        <Hash className="w-3 h-3 text-white/40" />
                        <span className="text-xs text-white/50">{standup.slack_channel}</span>
                    </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${isToday
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-white/10 text-white/60'
                    }`}>
                    {formatDate(scheduledDate)}
                </span>
            </div>

            <div className="flex items-center gap-4 text-sm text-white/60">
                <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    <span>{formatTime(scheduledDate)}</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4" />
                    <span>{standup.member_count} members</span>
                </div>
            </div>
        </div>
    );
}
