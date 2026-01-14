import React, { useState, useMemo } from 'react';
import SignalCard from './SignalCard';
import { IconHistory } from './Icons';
import './HistoryView.css';

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
            {/* Header Redesign */}
            {/* Header Redesign */}
            <div className="history-header">
                <div className="history-header-main">
                    <div className="history-title-group">
                        <div className="history-icon-wrapper">
                            <IconHistory size={28} />
                        </div>
                        <div>
                            <h2 className="history-title">Histórico de Sinais</h2>
                            <p className="history-subtitle">Registro das últimas 24 horas</p>
                        </div>
                    </div>
                    <div className="history-badge">
                        <div className="dot"></div>
                        {stats.total} Sinais
                    </div>
                </div>

                {/* Mobile Compact Stats Bar */}
                <div className="mobile-header-stats">
                    <div className="m-stat-item">
                        <span className="m-label">WIN</span>
                        <span className="m-value highlight">{stats.winRate}%</span>
                    </div>
                    <div className="m-divider"></div>
                    <div className="m-stat-item">
                        <span className="m-label">ROI</span>
                        <span className={`m-value ${parseFloat(stats.totalROI) >= 0 ? 'win' : 'loss'}`}>
                            {stats.totalROI > 0 ? '+' : ''}{stats.totalROI}%
                        </span>
                    </div>
                    <div className="m-divider"></div>
                    <div className="m-stat-item">
                        <span className="m-label">G</span>
                        <span className="m-value win">{stats.gains}</span>
                    </div>
                    <div className="m-divider"></div>
                    <div className="m-stat-item">
                        <span className="m-label">L</span>
                        <span className="m-value loss">{stats.losses}</span>
                    </div>
                </div>
            </div>

            {/* Performance Stats */}
            {stats.total > 0 && (
                <div className="history-stats-grid">
                    <div className="h-stat-card win">
                        <span className="h-stat-label">Ganhos (TP)</span>
                        <span className="h-stat-value">{stats.gains}</span>
                        <span className="h-stat-detail">+{stats.avgGain}% avg</span>
                    </div>
                    <div className="h-stat-card loss">
                        <span className="h-stat-label">Perdas (SL)</span>
                        <span className="h-stat-value">{stats.losses}</span>
                        <span className="h-stat-detail">{stats.avgLoss}% avg</span>
                    </div>
                    <div className="h-stat-card rate">
                        <span className="h-stat-label">Win Rate</span>
                        <span className="h-stat-value">{stats.winRate}%</span>
                    </div>
                    <div className={`h-stat-card ${parseFloat(stats.totalROI) >= 0 ? 'win' : 'loss'}`}>
                        <span className="h-stat-label">ROI Total</span>
                        <span className="h-stat-value">{stats.totalROI > 0 ? '+' : ''}{stats.totalROI}%</span>
                    </div>
                </div>
            )}

            {/* Clean Filter Tabs */}
            <div className="history-controls">
                <button
                    className={`h-tab ${activeFilter === 'ALL' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('ALL')}
                >
                    Todos
                </button>
                <button
                    className={`h-tab gain ${activeFilter === 'GAINS' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('GAINS')}
                >
                    Gains
                </button>
                <button
                    className={`h-tab loss ${activeFilter === 'LOSSES' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('LOSSES')}
                >
                    Losses
                </button>
            </div>

            {filteredHistory.length === 0 ? (
                <div className="history-empty">
                    <div className="empty-icon-circle">
                        <IconHistory size={32} />
                    </div>
                    <h3 className="empty-title">
                        {activeFilter === 'ALL' ? 'Nenhum sinal no histórico' : `Nenhum sinal de ${activeFilter.toLowerCase()}`}
                    </h3>
                    <p className="empty-text">
                        Sinais finalizados aparecerão aqui automaticamente.
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
