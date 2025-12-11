import { useState, useEffect } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
} from 'recharts';
import { getBlockedTrend, getEscalationTrend } from '../../api/client';

export default function AnalyticsCharts() {
    const [blockedData, setBlockedData] = useState<any[]>([]);
    const [escalationData, setEscalationData] = useState<any[]>([]);
    const [activeChart, setActiveChart] = useState<'blocked' | 'escalations'>('blocked');

    useEffect(() => {
        Promise.all([getBlockedTrend(14), getEscalationTrend(14)])
            .then(([blocked, escalations]) => {
                setBlockedData(blocked);
                setEscalationData(escalations);
            })
            .catch(console.error);
    }, []);

    // Mock data for demo
    const mockBlockedData = [
        { date: 'Dec 1', total: 12, blocked: 2 },
        { date: 'Dec 2', total: 15, blocked: 3 },
        { date: 'Dec 3', total: 10, blocked: 1 },
        { date: 'Dec 4', total: 18, blocked: 4 },
        { date: 'Dec 5', total: 14, blocked: 2 },
        { date: 'Dec 6', total: 20, blocked: 5 },
        { date: 'Dec 7', total: 16, blocked: 3 },
    ];

    const mockEscalationData = [
        { date: 'Dec 1', escalations: 1 },
        { date: 'Dec 2', escalations: 2 },
        { date: 'Dec 3', escalations: 0 },
        { date: 'Dec 4', escalations: 3 },
        { date: 'Dec 5', escalations: 1 },
        { date: 'Dec 6', escalations: 2 },
        { date: 'Dec 7', escalations: 1 },
    ];

    const chartData = blockedData.length > 0 ? blockedData : mockBlockedData;
    const escData = escalationData.length > 0 ? escalationData : mockEscalationData;

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">Analytics</h3>
                <div className="flex gap-2">
                    <button
                        onClick={() => setActiveChart('blocked')}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeChart === 'blocked'
                                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                : 'text-white/60 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        Blocked Trend
                    </button>
                    <button
                        onClick={() => setActiveChart('escalations')}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeChart === 'escalations'
                                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                : 'text-white/60 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        Escalations
                    </button>
                </div>
            </div>

            <div className="h-64">
                {activeChart === 'blocked' ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" fontSize={12} />
                            <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(15, 15, 35, 0.95)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '12px',
                                    color: 'white',
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="total"
                                stroke="#6366f1"
                                fillOpacity={1}
                                fill="url(#colorTotal)"
                                strokeWidth={2}
                                name="Total Issues"
                            />
                            <Area
                                type="monotone"
                                dataKey="blocked"
                                stroke="#ef4444"
                                fillOpacity={1}
                                fill="url(#colorBlocked)"
                                strokeWidth={2}
                                name="Blocked"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={escData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" fontSize={12} />
                            <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(15, 15, 35, 0.95)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '12px',
                                    color: 'white',
                                }}
                            />
                            <Bar
                                dataKey="escalations"
                                fill="url(#barGradient)"
                                radius={[4, 4, 0, 0]}
                                name="Escalations"
                            />
                            <defs>
                                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#f59e0b" />
                                    <stop offset="100%" stopColor="#d97706" />
                                </linearGradient>
                            </defs>
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
