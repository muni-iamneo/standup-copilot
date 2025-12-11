import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Bell, Search, CheckCircle, XCircle } from 'lucide-react';
import { checkIntegrationHealth } from '../../api/client';

const pageTitles: Record<string, string> = {
    '/': 'Dashboard',
    '/dashboard': 'Dashboard',
    '/config': 'Schedule Standup',
    '/history': 'Standup History',
    '/settings': 'Settings',
};

export default function Navbar() {
    const location = useLocation();
    const [health, setHealth] = useState<{ linear: boolean; slack: boolean } | null>(null);

    useEffect(() => {
        checkIntegrationHealth()
            .then(setHealth)
            .catch(() => setHealth({ linear: false, slack: false }));
    }, []);

    const pageTitle = pageTitles[location.pathname] || 'StandupCopilot';

    return (
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
            {/* Page Title */}
            <div>
                <h2 className="text-xl font-semibold text-gray-900">{pageTitle}</h2>
                <p className="text-xs text-gray-500">
                    {new Date().toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                    })}
                </p>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-4">
                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search..."
                        className="w-64 pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                    />
                </div>

                {/* Integration Status */}
                {/* <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-200">
                    <div className="flex items-center gap-1.5">
                        {health?.linear ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                        )}
                        <span className="text-xs font-medium text-gray-600">Linear</span>
                    </div>
                    <div className="w-px h-4 bg-gray-200" />
                    <div className="flex items-center gap-1.5">
                        {health?.slack ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                        )}
                        <span className="text-xs font-medium text-gray-600">Slack</span>
                    </div>
                </div> */}

                {/* Notifications */}
                <button className="relative p-2 rounded-xl bg-gray-50 border border-gray-200 hover:bg-gray-100 transition-colors">
                    <Bell className="w-5 h-5 text-gray-500" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                </button>
            </div>
        </header>
    );
}
