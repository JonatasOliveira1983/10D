import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OpeningPage from './components/OpeningPage';


import BancaPage from './components/Banca/BancaPage'; // Restored the complete version
import SignalJourney from './components/SignalJourney';
import SettingsPage from './components/SettingsPage';
import AgentsView from './components/AgentsView';
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
    const [currentPage, setCurrentPage] = useState('signal-journey');
    const [pinnedSymbol, setPinnedSymbol] = useState(null);
    const [btcRegime, setBtcRegime] = useState(null);

    // Initial URL Routing
    useEffect(() => {
        const path = window.location.pathname;
        if (path === '/btcanalises' || path === '/banca') {
            setShowOpening(false);
            setCurrentPage('banca');
        } else if (path === '/journey') {
            setShowOpening(false);
            setCurrentPage('signal-journey');
        }
    }, []);

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
                fetchHistory(1000, 240),
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
                            {currentPage === 'signal-journey' && (
                                <SignalJourney
                                    signals={signals}
                                    history={history}
                                    loading={loading}
                                />
                            )}
                            {currentPage === 'banca' && (
                                <BancaPage />
                            )}

                            {currentPage === 'settings' && (
                                <SettingsPage
                                    theme={theme}
                                    onToggleTheme={toggleTheme}
                                />
                            )}
                            {currentPage === 'agents' && (
                                <AgentsView />
                            )}
                        </main>
                    </div>
                </>
            )}
        </div>
    );
}
