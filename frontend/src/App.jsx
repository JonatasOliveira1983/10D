import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import OpeningPage from './components/OpeningPage';
import TradesOrganizerPage from './components/TradesOrganizer/TradesOrganizerPage';
import HistoryView from './components/HistoryView';
import AIAnalytics from './components/AIAnalytics';
import MLPerformance from './components/MLPerformance';
import { fetchSignals, fetchStats, fetchHistory, fetchBTCRegime } from './services/api';

const POLL_INTERVAL = 5000; // 5 seconds

export default function App() {
    const [showOpening, setShowOpening] = useState(true);
    const [signals, setSignals] = useState([]);
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState({
        monitored_pairs: 0,
        active_signals: 0,
        long_signals: 0,
        short_signals: 0,
        average_score: 0
    });
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const [theme, setTheme] = useState('dark');
    const [currentPage, setCurrentPage] = useState('dashboard');
    const [pinnedSymbol, setPinnedSymbol] = useState(null);
    const [btcRegime, setBtcRegime] = useState(null);

    // Toggle theme
    const toggleTheme = () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    // Fetch data
    const fetchData = useCallback(async () => {
        try {
            const [signalsData, statsData, historyData, regimeData] = await Promise.all([
                fetchSignals(),
                fetchStats(),
                fetchHistory(20),
                fetchBTCRegime()
            ]);

            setSignals(signalsData.signals || []);
            setStats(statsData);
            setHistory(historyData.history || []);
            setBtcRegime(regimeData);
            setLoading(false);
            setIsConnected(true);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
            setIsConnected(false);
        }
    }, []);

    // Pin/Unpin signal
    const handlePin = (symbol) => {
        setPinnedSymbol(prev => prev === symbol ? null : symbol);
    };

    // Sort signals: pinned first, then by score
    const processedSignals = useMemo(() => {
        if (!signals) return [];
        return [...signals].sort((a, b) => {
            if (a.symbol === pinnedSymbol) return -1;
            if (b.symbol === pinnedSymbol) return 1;
            return (b.score || 0) - (a.score || 0);
        });
    }, [signals, pinnedSymbol]);

    // Initial fetch and polling
    useEffect(() => {
        fetchData();

        const interval = setInterval(fetchData, POLL_INTERVAL);

        return () => clearInterval(interval);
    }, [fetchData]);

    // Set initial theme
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, []);

    return (
        <div className="app">
            {showOpening && <OpeningPage onEnter={() => setShowOpening(false)} />}

            {!showOpening && (
                <>
                    <Sidebar
                        currentPage={currentPage}
                        onNavigate={setCurrentPage}
                        theme={theme}
                        onToggleTheme={toggleTheme}
                        onLogout={() => setShowOpening(true)}
                    />

                    <div className="app-main">
                        <Header
                            stats={stats}
                            isConnected={isConnected}
                            btcRegime={btcRegime}
                        />

                        <main className="main-content">
                            {currentPage === 'dashboard' && (
                                <Dashboard
                                    signals={processedSignals}
                                    pinnedSymbol={pinnedSymbol}
                                    onPin={handlePin}
                                    loading={loading}
                                />
                            )}
                            {currentPage === 'organizer' && (
                                <TradesOrganizerPage />
                            )}
                            {currentPage === 'history' && (
                                <HistoryView
                                    history={history}
                                    loading={loading}
                                />
                            )}
                            {currentPage === 'ai' && (
                                <AIAnalytics />
                            )}
                            {currentPage === 'ml' && (
                                <MLPerformance />
                            )}
                            {currentPage === 'settings' && (
                                <div className="page-placeholder">
                                    <h2>⚙️ Configurações</h2>
                                    <p>Em breve...</p>
                                </div>
                            )}
                        </main>
                    </div>
                </>
            )}
        </div>
    );
}
