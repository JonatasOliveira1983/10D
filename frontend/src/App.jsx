import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import MobileNav from './components/MobileNav';
import { fetchSignals, fetchStats } from './services/api';

const POLL_INTERVAL = 5000; // 5 seconds

export default function App() {
    const [signals, setSignals] = useState([]);
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

    // Toggle theme
    const toggleTheme = () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    // Fetch data
    const fetchData = useCallback(async () => {
        try {
            const [signalsData, statsData] = await Promise.all([
                fetchSignals(),
                fetchStats()
            ]);

            setSignals(signalsData.signals || []);
            setStats(statsData);
            setLoading(false);
            setIsConnected(true);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
            setIsConnected(false);
        }
    }, []);

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
            <Sidebar
                currentPage={currentPage}
                onNavigate={setCurrentPage}
                theme={theme}
                onToggleTheme={toggleTheme}
            />

            <div className="app-main">
                <Header
                    stats={stats}
                    isConnected={isConnected}
                />

                <main className="main-content">
                    {currentPage === 'dashboard' && (
                        <Dashboard
                            signals={signals}
                            loading={loading}
                        />
                    )}
                    {currentPage === 'history' && (
                        <div className="page-placeholder">
                            <h2>📜 Histórico de Sinais</h2>
                            <p>Em breve...</p>
                        </div>
                    )}
                    {currentPage === 'settings' && (
                        <div className="page-placeholder">
                            <h2>⚙️ Configurações</h2>
                            <p>Em breve...</p>
                        </div>
                    )}
                </main>
            </div>

            {/* Mobile bottom navigation */}
            <MobileNav
                currentPage={currentPage}
                onNavigate={setCurrentPage}
                theme={theme}
                onToggleTheme={toggleTheme}
            />
        </div>
    );
}
