import React from 'react';

export default function Header({ stats, isConnected, btcRegime }) {
    // Get regime badge class
    const getRegimeClass = () => {
        switch (btcRegime?.regime) {
            case 'RANGING': return 'regime-ranging';
            case 'BREAKOUT': return 'regime-breakout';
            default: return 'regime-trending';
        }
    };

    return (
        <header className="header">
            <div className="header-content">
                <div className="header-title">
                    <img src="/logo10D.png" alt="10D" className="header-logo" />
                    <div className={`status-dot ${isConnected ? 'connected' : ''}`} title={isConnected ? 'Conectado' : 'Desconectado'}></div>
                </div>

                {/* BTC Regime Indicator */}
                {btcRegime && (
                    <div className={`btc-regime-indicator ${getRegimeClass()}`}>
                        <span className="regime-label">BTC</span>
                        <span className="regime-value">{btcRegime.regime}</span>
                        <div className="regime-targets">
                            <span className="target-item tp">TP {btcRegime.tp_pct}%</span>
                            <span className="target-item sl">SL {btcRegime.sl_pct}%</span>
                        </div>
                    </div>
                )}

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
