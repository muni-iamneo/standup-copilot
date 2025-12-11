import { Link } from 'react-router-dom';
import { Clock, AlertTriangle, ArrowUpRight } from 'lucide-react';
import type { StandupHistory } from '../../types';

interface Props {
    history: StandupHistory[];
}

export default function StandupHistoryTable({ history }: Props) {
    if (history.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-white/50">No standup history yet</p>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="border-b border-white/10">
                        <th className="table-header">Team</th>
                        <th className="table-header">Date</th>
                        <th className="table-header">Duration</th>
                        <th className="table-header">Issues</th>
                        <th className="table-header">Blocked</th>
                        <th className="table-header">Escalations</th>
                        <th className="table-header"></th>
                    </tr>
                </thead>
                <tbody>
                    {history.map((item) => (
                        <tr key={item.id} className="table-row">
                            <td className="table-cell font-medium text-white">
                                {item.team_name}
                            </td>
                            <td className="table-cell text-white/60">
                                {new Date(item.completed_at).toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: 'numeric',
                                    minute: '2-digit',
                                })}
                            </td>
                            <td className="table-cell">
                                <div className="flex items-center gap-1.5 text-white/60">
                                    <Clock className="w-4 h-4" />
                                    {item.duration_minutes ? `${item.duration_minutes}m` : '-'}
                                </div>
                            </td>
                            <td className="table-cell">
                                <span className="px-2 py-1 text-xs font-medium bg-blue-500/20 text-blue-400 rounded-full">
                                    {item.total_issues}
                                </span>
                            </td>
                            <td className="table-cell">
                                {item.blocked_count > 0 ? (
                                    <span className="px-2 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded-full">
                                        {item.blocked_count}
                                    </span>
                                ) : (
                                    <span className="text-white/40">-</span>
                                )}
                            </td>
                            <td className="table-cell">
                                {item.escalation_count > 0 ? (
                                    <div className="flex items-center gap-1 text-yellow-400">
                                        <AlertTriangle className="w-4 h-4" />
                                        {item.escalation_count}
                                    </div>
                                ) : (
                                    <span className="text-white/40">-</span>
                                )}
                            </td>
                            <td className="table-cell">
                                <Link
                                    to={`/standup/${item.id}`}
                                    className="p-2 rounded-lg hover:bg-white/10 text-white/40 hover:text-white transition-colors inline-flex"
                                >
                                    <ArrowUpRight className="w-4 h-4" />
                                </Link>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
