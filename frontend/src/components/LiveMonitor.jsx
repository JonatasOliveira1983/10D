import React, { useMemo, useState, useEffect } from 'react';
import './LiveMonitor.css';

// Key for localStorage persistence
const PINNED_SIGNALS_KEY = 'liveMonitor_pinnedSignals';
const ITEMS_PER_PAGE = 6;

export default function LiveMonitor({ signals, loading }) {
    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);

    // Load pinned signals from localStorage
    const [pinnedSignals, setPinnedSignals] = useState(() => {
        try {
            const saved = localStorage.getItem(PINNED_SIGNALS_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    });

    // Save to localStorage when pinned signals change
    useEffect(() => {
        localStorage.setItem(PINNED_SIGNALS_KEY, JSON.stringify(pinnedSignals));
    }, [pinnedSignals]);

    // Toggle pin status for a signal
    const togglePin = (signalId) => {
        setPinnedSignals(prev => {
            if (prev.includes(signalId)) {
                return prev.filter(id => id !== signalId);
            } else {
                return [...prev, signalId];
            }
        });
    };

    // Filter active signals and sort with pinned first
    const sortedSignals = useMemo(() => {
        const activeSignals = signals.filter(s => s.status === 'ACTIVE' || !s.status);

        return activeSignals.sort((a, b) => {
            const aIsPinned = pinnedSignals.includes(a.id);
            const bIsPinned = pinnedSignals.includes(b.id);

            // Pinned signals come first
            if (aIsPinned && !bIsPinned) return -1;
            if (!aIsPinned && bIsPinned) return 1;

            // Then sort by highest ROI
            return (b.highest_roi || 0) - (a.highest_roi || 0);
        });
    }, [signals, pinnedSignals]);

    // Pagination calculations
    const totalPages = Math.ceil(sortedSignals.length / ITEMS_PER_PAGE);

    const paginatedSignals = useMemo(() => {
        const start = (currentPage - 1) * ITEMS_PER_PAGE;
        return sortedSignals.slice(start, start + ITEMS_PER_PAGE);
    }, [sortedSignals, currentPage]);

    // Reset page if signals change and page is out of bounds
    useEffect(() => {
        if (currentPage > totalPages && totalPages > 0) {
            setCurrentPage(1);
        }
    }, [sortedSignals.length, totalPages, currentPage]);

    const calculateProgress = (roi) => {
        const progress = Math.min(100, Math.max(0, (roi / 6) * 100));
        return progress;
    };

    if (loading) {
        return <div className="live-monitor-loading">Carregando monitoramento em tempo real...</div>;
    }

    return (
        <div className="live-monitor">
            <div className="live-monitor-header">
                <h1>Live Sniper Monitor</h1>
                <p>Acompanhando oportunidades de 6% em tempo real</p>
                <div className="header-badges">
                    {pinnedSignals.length > 0 && (
                        <span className="pinned-count">{pinnedSignals.length} fixado(s)</span>
                    )}
                    {sortedSignals.length > 0 && (
                        <span className="total-count">{sortedSignals.length} sinal(is) ativo(s)</span>
                    )}
                </div>
            </div>

            <div className="monitor-grid">
                {paginatedSignals.length === 0 ? (
                    <div className="no-trades">Nenhum sinal ativo no momento. Aguardando próximas oportunidades...</div>
                ) : (
                    paginatedSignals.map(signal => {
                        const highestRoi = signal.highest_roi || 0;
                        const currentRoi = signal.current_roi || 0;
                        const progress = calculateProgress(highestRoi);
                        const isPinned = pinnedSignals.includes(signal.id);

                        return (
                            <div key={signal.id} className={`monitor-card ${highestRoi >= 6 ? 'target-reached' : ''} ${isPinned ? 'pinned' : ''}`}>
                                <div className="card-top">
                                    <div className="symbol-info">
                                        <span className="symbol">{signal.symbol}</span>
                                        <span className={`direction ${signal.direction}`}>{signal.direction}</span>
                                    </div>
                                    <div className="card-actions">
                                        <button
                                            className={`pin-button ${isPinned ? 'pinned' : ''}`}
                                            onClick={() => togglePin(signal.id)}
                                            title={isPinned ? 'Desafixar' : 'Fixar no topo'}
                                        >
                                            {isPinned ? '📌' : '📍'}
                                        </button>
                                        <div className="score-badge">
                                            {signal.emoji} {signal.score}%
                                        </div>
                                    </div>
                                </div>

                                <div className="roi-display">
                                    <div className="roi-current">
                                        <span className={`roi-value ${currentRoi >= 0 ? 'positive' : 'negative'}`}>
                                            {currentRoi >= 0 ? '+' : ''}{currentRoi.toFixed(2)}%
                                        </span>
                                        <span className="roi-label">ROI Atual</span>
                                    </div>
                                    <div className="roi-highest">
                                        <span className="roi-value highest">{highestRoi.toFixed(2)}%</span>
                                        <span className="roi-label">Máximo</span>
                                    </div>
                                </div>

                                <div className="progress-container">
                                    <div className="progress-labels">
                                        <span>0%</span>
                                        <span>2% (Parcial)</span>
                                        <span>3% (Trailing)</span>
                                        <span>6% (Sniper)</span>
                                    </div>
                                    <div className="progress-bar-bg">
                                        <div
                                            className="progress-bar-fill"
                                            style={{ width: `${progress}%` }}
                                        ></div>
                                        <div className="marker partial" style={{ left: '33.3%' }} title="2% - TP Parcial"></div>
                                        <div className="marker trailing" style={{ left: '50%' }} title="3% - Trailing Stop"></div>
                                        <div className="marker sniper" style={{ left: '100%' }} title="6% - Target"></div>
                                    </div>
                                </div>

                                <div className="status-badges">
                                    {signal.partial_tp_hit && (
                                        <span className="badge partial">TP Parcial ✅</span>
                                    )}
                                    {signal.trailing_stop_active && (
                                        <span className="badge trailing">Trailing Stop 🔥</span>
                                    )}
                                    {highestRoi >= 6 && (
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
                                        <span className={`sl-value ${signal.trailing_stop_active ? 'trailing-active' : ''}`}>
                                            ${signal.stop_loss}
                                        </span>
                                    </div>
                                    <div className="detail">
                                        <span>Take Profit:</span>
                                        <span className="tp-value">${signal.take_profit}</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="pagination-controls">
                    <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                    >
                        ← Anterior
                    </button>
                    <span className="pagination-info">
                        Página {currentPage} de {totalPages}
                    </span>
                    <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                    >
                        Próximo →
                    </button>
                </div>
            )}
        </div>
    );
}
