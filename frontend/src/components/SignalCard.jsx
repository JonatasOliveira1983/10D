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
        'SMA_CROSSOVER': 'Cruzamento SMA',
        'TREND_PULLBACK': 'Pullback',
        'RSI_EXTREME': 'RSI Extremo'
    };
    return labels[type] || type;
}

export default function SignalCard({ signal }) {
    const direction = signal.direction.toLowerCase();
    const scoreClass = getScoreClass(signal.score);

    return (
        <div className={`signal-card ${direction}`}>
            {/* Header */}
            <div className="card-header">
                <div className="symbol-info">
                    <span className="symbol-name">{signal.symbol.replace('USDT', '')}</span>
                    <div className="symbol-meta">
                        <span className={`direction-badge ${direction}`}>
                            {signal.direction === 'LONG' ? '🚀 LONG' : '📉 SHORT'}
                        </span>
                        <span className="signal-type-label">
                            {getSignalTypeLabel(signal.signal_type)}
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

            {/* Prices */}
            <div className="price-info">
                <div className="price-item">
                    <div className="price-label">Entrada</div>
                    <div className="price-value entry">${formatPrice(signal.entry_price)}</div>
                </div>
                <div className="price-item">
                    <div className="price-label">Stop Loss (1%)</div>
                    <div className="price-value sl">${formatPrice(signal.stop_loss)}</div>
                </div>
                <div className="price-item">
                    <div className="price-label">Take Profit (2%)</div>
                    <div className="price-value tp">${formatPrice(signal.take_profit)}</div>
                </div>
            </div>

            {/* Indicators / Confirmations */}
            <div className="confirmations">
                <span className={`confirmation-badge ${signal.confirmations.sma_crossover || signal.confirmations.pullback ? 'active' : ''}`}>
                    <span className="icon">{(signal.confirmations.sma_crossover || signal.confirmations.pullback) ? '✓' : '○'}</span>
                    SMA 8/21
                </span>
                <span className={`confirmation-badge ${signal.confirmations.volume ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations.volume ? '✓' : '○'}</span>
                    Vol {signal.volume_ratio}x
                </span>
                {signal.rsi && (
                    <span className={`confirmation-badge ${signal.confirmations.rsi_extreme ? 'active' : ''}`}>
                        <span className="icon">{signal.confirmations.rsi_extreme ? '✓' : '○'}</span>
                        RSI {signal.rsi}
                    </span>
                )}
                <span className={`confirmation-badge ${signal.confirmations.pivot_trend ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations.pivot_trend ? '✓' : '○'}</span>
                    Pivot {signal.pivot_trend || 'N/A'}
                </span>
            </div>

            {/* S/R Info */}
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

            {/* Timestamp */}
            <div className="timestamp">
                {signal.timestamp_readable}
            </div>
        </div>
    );
}
