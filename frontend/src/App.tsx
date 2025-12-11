import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Common/Sidebar';
import Navbar from './components/Common/Navbar';
import DashboardPage from './pages/DashboardPage';
import ConfigPage from './pages/ConfigPage';
import StandupDetailPage from './pages/StandupDetailPage';
import StandupMeetingPage from './pages/StandupMeetingPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';

function App() {
    return (
        <Router>
            <Routes>
                {/* Meeting page is full-screen without sidebar */}
                <Route path="/meeting/:id" element={<StandupMeetingPage />} />

                {/* Regular pages with sidebar */}
                <Route path="/*" element={
                    <div className="min-h-screen flex">
                        <Sidebar />
                        <div className="flex-1 flex flex-col ml-64">
                            <Navbar />
                            <main className="flex-1 p-8 overflow-auto">
                                <Routes>
                                    <Route path="/" element={<DashboardPage />} />
                                    <Route path="/dashboard" element={<DashboardPage />} />
                                    <Route path="/config" element={<ConfigPage />} />
                                    <Route path="/standup/:id" element={<StandupDetailPage />} />
                                    <Route path="/history" element={<HistoryPage />} />
                                    <Route path="/settings" element={<SettingsPage />} />
                                </Routes>
                            </main>
                        </div>
                    </div>
                } />
            </Routes>
        </Router>
    );
}

export default App;

