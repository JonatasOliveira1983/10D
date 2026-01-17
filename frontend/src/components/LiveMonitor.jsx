import React, { useMemo } from 'react';
import './LiveMonitor.css';

export default function LiveMonitor({ signals, loading }) {
    const activeSignals = useMemo(() => {
        return signals.filter(s => s.status === 'ACTIVE' || !s.status);
    }, [signals]);

    const calculateProgress = (roi) => {
        // We map 0% to 6% as the main progress bar
        const progress = Math.min(100, Math.max(0, (roi / 6) * 100));
        return progress;
    };

    if (loading) {
        return <div className="live-monitor-loading">Carregando monitoramento em tempo real...</div>;
    }

    return (
        <div className="live-monitor">
            <div className="live-monitor-header">
                <h1>🎯 Live Sniper Monitor</h1>
                <p>Acompanhando oportunidades de 6% em tempo real</p>
            </div>

            <div className="monitor-grid">
                {activeSignals.length === 0 ? (
                    <div className="no-trades">Nenhum sinal ativo no momento. Aguardando próximas oportunidades...</div>
                ) : (
                    activeSignals.map(signal => {
                        const roi = signal.highest_roi || 0;
                        const currentRoi = signal.current_roi || 0; // Assuming we might pass current ROI too
                        const progress = calculateProgress(roi);

                        return (
                            <div key={signal.id} className={`monitor-card ${roi >= 6 ? 'target-reached' : ''}`}>
                                <div className="card-top">
                                    <div className="symbol-info">
                                        <span className="symbol">{signal.symbol}</span>
                                        <span className={`direction ${signal.direction}`}>{signal.direction}</span>
                                    </div>
                                    <div className="score-badge">
                                        {signal.emoji} {signal.score}%
                                    </div>
                                </div>

                                <div className="roi-display">
                                    <div className="roi-value">{roi.toFixed(2)}%</div>
                                    <div className="roi-label">Máximo Atingido</div>
                                </div>

                                <div className="progress-container">
                                    <div className="progress-labels">
                                        <span>0%</span>
                                        <span>3% (Trailing)</span>
                                        <span>6% (Sniper)</span>
                                    </div>
                                    <div className="progress-bar-bg">
                                        <div
                                            className="progress-bar-fill"
                                            style={{ width: `${progress}%` }}
                                        ></div>
                                        <div className="marker partial" style={{ left: '33.3%' }}></div>
                                        <div className="marker trailing" style={{ left: '50%' }}></div>
                                        <div className="marker sniper" style={{ left: '100%' }}></div>
                                    </div>
                                </div>

                                <div className="status-badges">
                                    {signal.partial_tp_hit && (
                                        <span className="badge partial">TP Parcial ✅</span>
                                    )}
                                    {signal.trailing_stop_active && (
                                        <span className="badge trailing">Trailing Stop 🔥</span>
                                    )}
                                    {roi >= 6 && (
                                        <span className="badge sniper">TARGET 6% 🎯</span>
                                    )}
                                </div>

                                <div className="price-details">
                                    <div className="detail">
                                        <span>Entrada:</span>
                                        <span>${signal.entry_price}</span>
                                    </div>
                                    <div className="detail">
                                        <span>Stop Atual:</span>
                                        <span className="sl-value">${signal.stop_loss}</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
