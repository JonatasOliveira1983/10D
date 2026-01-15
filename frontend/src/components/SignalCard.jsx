import React from 'react'; // Force deploy update

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'strong';
    if (score >= 55) return 'good';
    if (score >= 40) return 'moderate';
    return 'weak';
}

function formatPrice(price) {
    if (price === undefined || price === null) return '0.00';
    // Se o preço for muito pequeno, garantimos que não apareça em notação científica
    if (price < 0.0001) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 });
    return price.toString();
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

function formatReadableTimestamp(readableStr) {
    if (!readableStr) return '';
    try {
        // Assume format "YYYY-MM-DD HH:MM:SS"
        const parts = readableStr.split(' ');
        if (parts.length < 2) return readableStr;
        const dateParts = parts[0].split('-');
        const timeParts = parts[1].split(':');

        const year = dateParts[0];
        const month = dateParts[1];
        const day = dateParts[2];
        const hour = timeParts[0];
        const minute = timeParts[1];

        return `${hour}:${minute} ${day}/${month}`;
    } catch (e) {
        return readableStr;
    }
}

export default function SignalCard({ signal, isPinned, onPin }) {
    const direction = signal.direction.toLowerCase();
    const scoreClass = getScoreClass(signal.score);
    const status = signal.status || 'ACTIVE';
    const isFinalized = status !== 'ACTIVE';
    const displayTime = isFinalized ? signal.exit_timestamp_readable : signal.timestamp_readable;

    return (
        <div className={`signal-card ${direction} ${isFinalized ? 'finalized ' + status.toLowerCase().replace('_', '-') : ''}`}>
            {/* Header */}
            <div className="card-header">
                <div className="symbol-info">
                    <span className="symbol-name">{(signal.symbol || '').replace('USDT', '')}</span>
                    <div className="symbol-meta">
                        <span className={`direction-badge ${direction}`}>
                            {signal.direction === 'LONG' ? 'LONG' : 'SHORT'}
                        </span>
                        <span className={`status-badge ${status.toLowerCase().replace('_', '-')}`}>
                            {status === 'ACTIVE' ? 'ATIVO' :
                                status === 'TP_HIT' ? 'ALVO ATINGIDO' :
                                    status === 'EXPIRED' ? 'EXPIRADO' :
                                        status === 'VOL_CLIMAX' ? 'EXAUSTÃO VOL' : 'STOP LOSS'}
                        </span>
                    </div>
                </div>

                <div className="card-right-header">
                    {status === 'ACTIVE' && signal.entry_zone && (
                        <div className={`entry-zone-badge ${signal.entry_zone.toLowerCase()}`}>
                            <span className="dot"></span>
                            {signal.entry_zone === 'IDEAL' && 'ENTRADA IDEAL'}
                            {signal.entry_zone === 'WAIT' && 'AGUARDE PULLBACK'}
                            {signal.entry_zone === 'LATE' && 'ENTRADA JÁ PASSOU'}
                            {signal.entry_zone === 'NEAR' && 'PRÓXIMO DA ENTRADA'}
                        </div>
                    )}



                    {/* Unified Score + ML Badge */}
                    <div className="unified-score-badge">
                        {signal.ml_probability !== null && signal.ml_probability !== undefined ? (
                            <>
                                {/* Show Rules Score if ML is default (0.5) */}
                                {signal.score_breakdown && signal.score_breakdown.rules_score ? (
                                    <>
                                        <div className="score-ml-row">
                                            <span className="ml-label">Rules</span>
                                            <span className={`score-value-inline ${getScoreClass(signal.score_breakdown.rules_score)}`}>
                                                {signal.score_breakdown.rules_score.toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="score-ml-row">
                                            <span className="ml-label">ML</span>
                                            <span className={`ml-value ${signal.ml_probability >= 0.70 ? 'high' : signal.ml_probability >= 0.50 ? 'medium' : 'low'}`}>
                                                {(signal.ml_probability * 100).toFixed(0)}%
                                                {signal.ml_probability === 0.5 && <span style={{ fontSize: '0.6rem', opacity: 0.5 }}> *</span>}
                                            </span>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="score-ml-row">
                                            <span className="ml-label">ML</span>
                                            <span className={`ml-value ${signal.ml_probability >= 0.70 ? 'high' : signal.ml_probability >= 0.50 ? 'medium' : 'low'}`}>
                                                {(signal.ml_probability * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="score-ml-row">
                                            <span className="ml-label">Score</span>
                                            <span className={`score-value-inline ${scoreClass}`}>
                                                {signal.score.toFixed(0)}%
                                            </span>
                                        </div>
                                    </>
                                )}
                            </>
                        ) : (
                            <>
                                <span className={`score-value-compact ${scoreClass}`}>
                                    {signal.score.toFixed(0)}%
                                </span>
                                <div className="score-bar">
                                    <div
                                        className={`score-bar-fill ${scoreClass}`}
                                        style={{ width: `${signal.score || 0}%` }}
                                    ></div>
                                </div>
                            </>
                        )}
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
                    <div className="price-value entry-large">${formatPrice(signal.entry_price)}</div>
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
                <span className={`confirmation-badge ${signal.confirmations?.ema_crossover || signal.confirmations?.pullback ? 'active' : ''}`}>
                    <span className="icon">{(signal.confirmations?.ema_crossover || signal.confirmations?.pullback) ? '✓' : '○'}</span>
                    EMA
                </span>
                <span className={`confirmation-badge ${signal.confirmations?.macd ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations?.macd ? '✓' : '○'}</span>
                    MACD
                </span>
                <span className={`confirmation-badge ${signal.confirmations?.volume ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations?.volume ? '✓' : '○'}</span>
                    Vol {signal.volume_ratio || 0}x
                </span>
                <span className={`confirmation-badge ${signal.confirmations?.trend_4h ? 'active' : ''}`}>
                    <span className="icon">{signal.confirmations?.trend_4h ? '✓' : '○'}</span>
                    4H
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
                        {signal.institutional.absorption && (
                            <span className={`confirmation-badge ${signal.institutional.absorption?.confirmed ? 'active' : ''}`}>
                                <span className="icon">{signal.institutional.absorption?.confirmed ? '✓' : '○'}</span>
                                Absorção
                            </span>
                        )}
                        <span className={`confirmation-badge ${signal.institutional.rsi_crossover_btc || signal.confirmations?.rsi_crossover_btc ? 'active' : ''}`}>
                            <span className="icon">{(signal.institutional.rsi_crossover_btc || signal.confirmations?.rsi_crossover_btc) ? '✓' : '○'}</span>
                            RSI×BTC
                        </span>
                        <span className={`confirmation-badge ${signal.institutional.liquidity_aligned || signal.confirmations?.liquidity_aligned ? 'active' : ''}`}>
                            <span className="icon">{(signal.institutional.liquidity_aligned || signal.confirmations?.liquidity_aligned) ? '🐋' : '○'}</span>
                            Liq{signal.institutional.liquidity_hunt === 'LONG_HUNT' ? '↓' : signal.institutional.liquidity_hunt === 'SHORT_HUNT' ? '↑' : ''}
                        </span>
                    </>
                )}
            </div>

            {/* S/R Info */}
            {!isFinalized && (
                <div className="sr-info">
                    <div className={`sr-zone ${signal.sr_zone?.toLowerCase() || 'neutral'}`}>
                        {signal.sr_zone === 'RESISTANCE' && 'Resistência'}
                        {signal.sr_zone === 'SUPPORT' && 'Suporte'}
                        {(signal.sr_zone === 'NEUTRAL' || !signal.sr_zone) && 'Neutro'}
                    </div>
                    <span className={`sr-alignment ${signal.sr_alignment?.toLowerCase() || 'misaligned'}`}>
                        {signal.sr_alignment === 'ALIGNED' && '✓ Alinhado'}
                        {signal.sr_alignment !== 'ALIGNED' && '✗ Desalinhado'}
                    </span>
                </div>
            )}

            {/* Timestamp */}
            <div
                className={`timestamp-highlight ${isPinned ? 'pinned' : ''}`}
                onClick={onPin}
                title={isPinned ? "Desafixar sinal" : "Fixar sinal no topo"}
            >
                {isPinned ? '📌' : '🕒'} {formatReadableTimestamp(displayTime)}
            </div>
        </div>
    );
}
