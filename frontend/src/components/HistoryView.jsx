import React, { useState, useMemo } from 'react';
import SignalCard from './SignalCard';

export default function HistoryView({ history, loading }) {
    const [activeFilter, setActiveFilter] = useState('ALL');

    // Calculate stats
    const stats = useMemo(() => {
        const gains = history.filter(s => s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX');
        const losses = history.filter(s => s.status === 'SL_HIT');

        const total = history.length;
        const winRate = total > 0 ? ((gains.length / total) * 100).toFixed(1) : 0;

        // Calculate total ROI
        const totalROI = history.reduce((acc, s) => acc + (s.final_roi || 0), 0);
        const avgROI = total > 0 ? (totalROI / total).toFixed(2) : 0;

        // Calculate avg gain and avg loss
        const avgGain = gains.length > 0
            ? (gains.reduce((acc, s) => acc + (s.final_roi || 0), 0) / gains.length).toFixed(2)
            : 0;
        const avgLoss = losses.length > 0
            ? (losses.reduce((acc, s) => acc + (s.final_roi || 0), 0) / losses.length).toFixed(2)
            : 0;

        return {
            total,
            gains: gains.length,
            losses: losses.length,
            winRate,
            totalROI: totalROI.toFixed(2),
            avgROI,
            avgGain,
            avgLoss
        };
    }, [history]);

    // Filter history based on active filter
    const filteredHistory = useMemo(() => {
        switch (activeFilter) {
            case 'GAINS':
                return history.filter(s => s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX');
            case 'LOSSES':
                return history.filter(s => s.status === 'SL_HIT');
            default:
                return history;
        }
    }, [history, activeFilter]);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <div className="loading-text">Carregando histórico...</div>
            </div>
        );
    }

    return (
        <div className="history-view">
            <h2 className="section-title">
                📜 Histórico de Sinais ({stats.total})
            </h2>

            {/* Performance Stats */}
            {stats.total > 0 && (
                <div className="history-stats">
                    <div className="stat-card win">
                        <span className="stat-label">Ganhos (TP)</span>
                        <span className="stat-value">{stats.gains}</span>
                        <span className="stat-detail">+{stats.avgGain}% avg</span>
                    </div>
                    <div className="stat-card loss">
                        <span className="stat-label">Perdas (SL)</span>
                        <span className="stat-value">{stats.losses}</span>
                        <span className="stat-detail">{stats.avgLoss}% avg</span>
                    </div>
                    <div className="stat-card rate">
                        <span className="stat-label">Win Rate</span>
                        <span className="stat-value">{stats.winRate}%</span>
                    </div>
                    <div className={`stat-card ${parseFloat(stats.totalROI) >= 0 ? 'win' : 'loss'}`}>
                        <span className="stat-label">ROI Total</span>
                        <span className="stat-value">{stats.totalROI > 0 ? '+' : ''}{stats.totalROI}%</span>
                    </div>
                </div>
            )}

            {/* Filter Tabs */}
            <div className="filter-tabs">
                <button
                    className={`filter-tab ${activeFilter === 'ALL' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('ALL')}
                >
                    Todos ({stats.total})
                </button>
                <button
                    className={`filter-tab gain ${activeFilter === 'GAINS' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('GAINS')}
                >
                    ✓ Gains ({stats.gains})
                </button>
                <button
                    className={`filter-tab loss ${activeFilter === 'LOSSES' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('LOSSES')}
                >
                    ✗ Losses ({stats.losses})
                </button>
            </div>

            {filteredHistory.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📂</div>
                    <h3 className="empty-title">
                        {activeFilter === 'ALL' ? 'Nenhum sinal no histórico' : `Nenhum sinal ${activeFilter.toLowerCase()}`}
                    </h3>
                    <p className="empty-text">
                        Sinais finalizados aparecerão aqui.
                    </p>
                </div>
            ) : (
                <div className="signals-grid">
                    {filteredHistory.map((signal) => (
                        <SignalCard key={signal.id} signal={signal} />
                    ))}
                </div>
            )}
        </div>
    );
}
