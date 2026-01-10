import React from 'react';

export default function Header({ stats, isConnected }) {
    return (
        <header className="header">
            <div className="header-content">
                <div className="header-title">
                    <img src="/logo10D.png" alt="10D" className="header-logo" />
                    <div className={`status-dot ${isConnected ? 'connected' : ''}`} title={isConnected ? 'Conectado' : 'Desconectado'}></div>
                </div>

                <div className="header-stats">
                    <div className="stat-item">
                        <span className="stat-value">{stats.monitored_pairs}</span>
                        <span className="stat-label">Pares</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{stats.active_signals}</span>
                        <span className="stat-label">Sinais</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value long">{stats.long_signals}</span>
                        <span className="stat-label">Long</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value short">{stats.short_signals}</span>
                        <span className="stat-label">Short</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{stats.average_score}</span>
                        <span className="stat-label">Score Avg</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{stats.total_historical}</span>
                        <span className="stat-label">Histórico</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
