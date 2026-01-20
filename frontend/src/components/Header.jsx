import React from 'react';

export default function Header({ stats, isConnected, btcRegime }) {
    // Get regime badge class
    const getRegimeClass = () => {
        switch (btcRegime?.regime) {
            case 'RANGING': return btcRegime.priority === 'sniper' ? 'regime-sniper' : 'regime-ranging';
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
                        <span className="regime-value">
                            {btcRegime.regime}
                            {btcRegime.priority === 'sniper' && <span className="sniper-badge">SNIPER MODE 🔥</span>}
                        </span>
                        <div className="regime-targets">
                            <span className="target-item price">
                                ${btcRegime.regime_details?.current_price?.toLocaleString()}
                            </span>
                            <span className={`target-item change ${btcRegime.change_24h >= 0 ? 'positive' : 'negative'}`}>
                                {btcRegime.change_24h >= 0 ? '+' : ''}{btcRegime.change_24h}%
                            </span>
                        </div>
                    </div>
                )}

                <div className="header-stats">
                    <div className="stat-item" title="Pares Monitorados">
                        <span className="stat-value">{stats.monitored_pairs}</span>
                        <span className="stat-label hide-mobile">Pares</span>
                    </div>
                    <div className="stat-item" title="Sinais Ativos">
                        <span className="stat-value">{stats.active_signals}</span>
                        <span className="stat-label hide-mobile">Sinais</span>
                    </div>
                    <div className="stat-item desktop-only">
                        <span className="stat-value long">{stats.long_signals}</span>
                        <span className="stat-label">Long</span>
                    </div>
                    <div className="stat-item desktop-only">
                        <span className="stat-value short">{stats.short_signals}</span>
                        <span className="stat-label">Short</span>
                    </div>
                    <div className="stat-item" title="Score Médio">
                        <span className="stat-value">{stats.average_score}</span>
                        <span className="stat-label hide-mobile">Score</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
