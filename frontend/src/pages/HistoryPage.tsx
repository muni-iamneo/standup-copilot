import { useState, useEffect } from 'react';
import { Search, Filter, Calendar, Download } from 'lucide-react';
import { getStandupHistory } from '../api/client';
import type { StandupHistory } from '../types';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import StandupHistoryTable from '../components/Dashboard/StandupHistoryTable';

export default function HistoryPage() {
    const [history, setHistory] = useState<StandupHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [dateFilter, setDateFilter] = useState(30);

    useEffect(() => {
        setLoading(true);
        getStandupHistory(dateFilter, 0, 50)
            .then(setHistory)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [dateFilter]);

    const filteredHistory = history.filter((item) =>
        item.team_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const totalIssues = history.reduce((sum, item) => sum + item.total_issues, 0);
    const totalBlocked = history.reduce((sum, item) => sum + item.blocked_count, 0);
    const totalEscalations = history.reduce((sum, item) => sum + item.escalation_count, 0);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Standup History</h1>
                    <p className="text-white/60">
                        View and analyze past standup meetings
                    </p>
                </div>
                <button className="btn-secondary flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card text-center">
                    <p className="text-3xl font-bold text-white">{history.length}</p>
                    <p className="text-sm text-white/50">Total Standups</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-blue-400">{totalIssues}</p>
                    <p className="text-sm text-white/50">Issues Discussed</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-red-400">{totalBlocked}</p>
                    <p className="text-sm text-white/50">Blocked Issues</p>
                </div>
                <div className="card text-center">
                    <p className="text-3xl font-bold text-yellow-400">{totalEscalations}</p>
                    <p className="text-sm text-white/50">Escalations</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                    <input
                        type="text"
                        placeholder="Search by team name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="input-field pl-10"
                    />
                </div>
                <div className="flex gap-2">
                    {[7, 14, 30, 90].map((days) => (
                        <button
                            key={days}
                            onClick={() => setDateFilter(days)}
                            className={`px-4 py-2 rounded-xl font-medium transition-all ${dateFilter === days
                                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                    : 'bg-white/5 text-white/60 border border-white/10 hover:bg-white/10'
                                }`}
                        >
                            <Calendar className="w-4 h-4 inline mr-1" />
                            {days}d
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="card">
                {loading ? (
                    <div className="flex items-center justify-center py-16">
                        <LoadingSpinner size="lg" text="Loading history..." />
                    </div>
                ) : (
                    <StandupHistoryTable history={filteredHistory} />
                )}
            </div>
        </div>
    );
}
