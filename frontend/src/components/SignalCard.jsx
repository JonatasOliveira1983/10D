import React from 'react';

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'strong';
    if (score >= 55) return 'good';
    if (score >= 40) return 'moderate';
    return 'weak';
}

function formatPrice(price) {
    if (price >= 1000) return price.toFixed(2);
    if (price >= 1) return price.toFixed(4);
    return price.toFixed(6);
}

function getSignalTypeLabel(type) {
    const labels = {
        'EMA_CROSSOVER': 'EMA 20/50 + MACD',
        'TREND_PULLBACK': 'Pullback',
        'RSI_BB_REVERSAL': 'RSI + Bollinger Reversão',
        'JUDAS_SWING': 'Institutional Judas Swing'
    };
    return labels[type] || type;
}

export default function SignalCard({ signal }) {
    const direction = signal.direction.toLowerCase();
    const scoreClass = getScoreClass(signal.score);
    const status = signal.status || 'ACTIVE';
    const isFinalized = status !== 'ACTIVE';

    return (
        <div className={`signal-card ${direction} ${isFinalized ? 'finalized ' + status.toLowerCase().replace('_', '-') : ''}`}>
            {/* Header */}
            <div className="card-header">
                <div className="symbol-info">
                    <span className="symbol-name">{signal.symbol.replace('USDT', '')}</span>
                    <div className="symbol-meta">
                        <span className={`direction-badge ${direction}`}>
                            {signal.direction === 'LONG' ? '🚀 LONG' : '📉 SHORT'}
                        </span>
                        <span className={`status-badge ${status.toLowerCase().replace('_', '-')}`}>
                            {status === 'ACTIVE' ? '⏱ ATIVO' : status === 'TP_HIT' ? '🎯 ALVO ATINGIDO' : '🛑 STOP LOSS'}
                        </span>
                    </div>
                </div>

                <div className="score-container">
                    <span className={`score-value ${scoreClass}`}>
                        {signal.emoji} {signal.score}
                    </span>
                    <div className="score-bar">
                        <div
                            className={`score-bar-fill ${scoreClass}`}
                            style={{ width: `${signal.score}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Type Label */}
            <div style={{ marginBottom: '12px' }}>
                <span className="signal-type-label">
                    {getSignalTypeLabel(signal.signal_type)}
                </span>
            </div>

            {/* Prices & ROI */}
            <div className="price-info">
                <div className="price-item">
                    <div className="price-label">Entrada</div>
                    <div className="price-value entry">${formatPrice(signal.entry_price)}</div>
                </div>
                {isFinalized ? (
                    <>
                        <div className="price-item">
                            <div className="price-label">Saída</div>
                            <div className="price-value">${formatPrice(signal.exit_price)}</div>
                        </div>
                        <div className="price-item roi">
                            <div className="price-label">ROI Final</div>
                            <div className="price-value">{signal.final_roi > 0 ? '+' : ''}{signal.final_roi}%</div>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="price-item">
                            <div className="price-label">Stop Loss</div>
                            <div className="price-value sl">${formatPrice(signal.stop_loss)}</div>
                        </div>
                        <div className="price-item">
                            <div className="price-label">Take Profit</div>
                            <div className="price-value tp">${formatPrice(signal.take_profit)}</div>
                        </div>
                    </>
                )}
            </div>

            {/* Indicators / Confirmations */}
            <div className="confirmations">
                <span className={`confirmation-badge ${signal.confirmations.ema_crossover || signal.confirmations.pullback ? 'active' : ''}`}>
                    <span className="icon">{(signal.confirmations.ema_crossover || signal.confirmations.pullback) ? '✓' : '○'}</span>
                    EMA
                </span>
                <span className={`confirmation-badge ${signal.confirmations.macd ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations.macd ? '✓' : '○'}</span>
                    MACD
                </span>
                <span className={`confirmation-badge ${signal.confirmations.volume ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations.volume ? '✓' : '○'}</span>
                    Vol {signal.volume_ratio}x
                </span>

                {/* Institutional Confirmations */}
                {signal.institutional && (
                    <>
                        <span className={`confirmation-badge ${signal.institutional.cvd_divergence ? 'active' : ''}`}>
                            <span className="icon">{signal.institutional.cvd_divergence ? '✓' : '○'}</span>
                            CVD
                        </span>
                        <span className={`confirmation-badge ${signal.institutional.oi_accumulation ? 'active' : ''}`}>
                            <span className="icon">{signal.institutional.oi_accumulation ? '✓' : '○'}</span>
                            OI
                        </span>
                        <span className={`confirmation-badge ${signal.institutional.lsr_cleanup ? 'active' : ''}`}>
                            <span className="icon">{signal.institutional.lsr_cleanup ? '✓' : '○'}</span>
                            LSR
                        </span>
                        {signal.institutional.rs_score !== undefined && (
                            <span className={`confirmation-badge ${signal.institutional.rs_score > 0 ? 'active' : ''}`}>
                                <span className="icon">{signal.institutional.rs_score > 0 ? '✓' : '○'}</span>
                                RS {signal.institutional.rs_score > 0 ? '+' : ''}{signal.institutional.rs_score.toFixed(4)}
                            </span>
                        )}
                    </>
                )}

                <span className={`confirmation-badge ${signal.confirmations.trend_4h ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations.trend_4h ? '✓' : '○'}</span>
                    4H
                </span>
            </div>

            {/* S/R Info */}
            {!isFinalized && (
                <div className="sr-info">
                    <div className={`sr-zone ${signal.sr_zone.toLowerCase()}`}>
                        {signal.sr_zone === 'RESISTANCE' && '🔴 Resistência'}
                        {signal.sr_zone === 'SUPPORT' && '🟢 Suporte'}
                        {signal.sr_zone === 'NEUTRAL' && '⚪ Neutro'}
                    </div>
                    <span className={`sr-alignment ${signal.sr_alignment.toLowerCase()}`}>
                        {signal.sr_alignment === 'ALIGNED' && '✓ Alinhado'}
                        {signal.sr_alignment === 'MISALIGNED' && '✗ Desalinhado'}
                    </span>
                </div>
            )}

            {/* Timestamp */}
            <div className="timestamp">
                {isFinalized ? `Finalizado em: ${signal.exit_timestamp_readable}` : signal.timestamp_readable}
            </div>
        </div>
    );
}
