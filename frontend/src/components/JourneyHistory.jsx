import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './SignalJourney.css';
import './HistoryView.css';

// Reuse Icons from the system
const IconHistory = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
);

const PaginationControls = ({ currentPage, totalPages, onPageChange, t }) => {
    if (totalPages <= 1) return null;
    return (
        <div className="sj-pagination">
            <button className="pagination-btn" disabled={currentPage === 1} onClick={() => onPageChange(currentPage - 1)}>
                ← {t('signalJourney.prev')}
            </button>
            <span className="pagination-info">{currentPage} / {totalPages}</span>
            <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => onPageChange(currentPage + 1)}>
                {t('signalJourney.next')} →
            </button>
        </div>
    );
};

const HistoryCard = ({ signal, t }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const roi = signal.final_roi || signal.current_roi || 0;

    const formatDate = (ts) => {
        const d = new Date(ts);
        return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
    };

    return (
        <div className={`history-mobile-card ${isExpanded ? 'active' : ''}`} onClick={() => setIsExpanded(!isExpanded)}>
            <div className="card-main-info">
                <div className="info-left">
                    <span className="info-date">{formatDate(signal.timestamp)}</span>
                    <span className="info-symbol">{signal.symbol}</span>
                </div>
                <div className="info-right">
                    <span className={`info-roi ${roi >= 0 ? 'positive' : 'negative'}`}>
                        {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                    </span>
                    <span className={`info-status-dot ${signal.status.toLowerCase()}`} title={signal.status} />
                </div>
            </div>

            {isExpanded && (
                <div className="card-details">
                    <div className="detail-row">
                        <span>{t('signalJourney.type')}:</span>
                        <span>{signal.signal_type?.replace('_', ' ')}</span>
                    </div>
                    <div className="detail-row">
                        <span>{t('signalJourney.entry')}:</span>
                        <span>${signal.entry_price?.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                        <span>{t('signalJourney.result')}:</span>
                        <span className={roi >= 0 ? 'positive' : 'negative'}>{signal.status}</span>
                    </div>

                    {/* New Decision Report Section */}
                    {signal.decision_report && (
                        <div className="decision-report-section">
                            <div className="report-divider"></div>
                            <h4 className="report-title">Relatório de Decisão</h4>

                            <div className="report-grid">
                                <div className="report-item">
                                    <span className="report-label">Análise do Conselho (IA)</span>
                                    <p className="report-text">{signal.decision_report.council?.reasoning || 'N/A'}</p>
                                </div>

                                <div className="report-indicators-group">
                                    <div className="mini-stat">
                                        <span className="mini-label">RSI</span>
                                        <span className="mini-value">{signal.decision_report.technicals?.rsi?.toFixed(1) || 'N/A'}</span>
                                    </div>
                                    <div className="mini-stat">
                                        <span className="mini-label">CVD Delta</span>
                                        <span className="mini-value">{signal.decision_report.technicals?.cvd_delta || 'N/A'}</span>
                                    </div>
                                    <div className="mini-stat">
                                        <span className="mini-label">OI</span>
                                        <span className="mini-value text-truncate">{signal.decision_report.technicals?.open_interest || 'N/A'}</span>
                                    </div>
                                </div>

                                <div className="report-item mt-2">
                                    <span className="report-label">Narrativa de Mercado</span>
                                    <p className="report-text italic">
                                        {signal.decision_report.market?.news_summary || 'Sem notícias relevantes no momento.'}
                                        <br />
                                        <small className="text-muted">Regime: {signal.decision_report.market?.btc_regime || 'N/A'}</small>
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {!signal.decision_report && signal.llm_validation?.reasoning && (
                        <div className="detail-insight">
                            <p><strong>AI Insight:</strong> {signal.llm_validation.reasoning}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default function JourneyHistory({ history, loading }) {
    const { t } = useTranslation();
    const [currentPage, setCurrentPage] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilter, setActiveFilter] = useState('ALL');
    const ITEMS_PER_PAGE = 10;

    // Filter to last 10 days AND apply search/status filters
    const tenDaysAgo = Date.now() - (10 * 24 * 60 * 60 * 1000);

    // 1. Initial time filter
    const timeFilteredHistory = React.useMemo(() => {
        return history.filter(s => s.timestamp > tenDaysAgo);
    }, [history, tenDaysAgo]);

    // 2. Apply Search and Status Filters
    const filteredHistory = React.useMemo(() => {
        return timeFilteredHistory.filter(s => {
            // Status Filter
            const matchesFilter = activeFilter === 'ALL' ||
                (activeFilter === 'GAINS' && (s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX')) ||
                (activeFilter === 'LOSSES' && s.status === 'SL_HIT') ||
                (activeFilter === 'EXPIRED' && s.status === 'EXPIRED');

            // Search Filter (Normalize: remove .P, .X, spaces, special chars)
            if (searchTerm) {
                const normalize = (str) => (str || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
                const sSym = normalize(s.symbol);
                const query = normalize(searchTerm);

                // Check for exact match or substring
                if (!sSym.includes(query)) return false;
            }

            return matchesFilter;
        }).sort((a, b) => b.timestamp - a.timestamp);
    }, [timeFilteredHistory, activeFilter, searchTerm]);

    // 3. Calculate Stats based on FILTERED history
    const stats = React.useMemo(() => {
        const gains = filteredHistory.filter(s => s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX');
        const losses = filteredHistory.filter(s => s.status === 'SL_HIT');
        const expired = filteredHistory.filter(s => s.status === 'EXPIRED');

        const decisiveTotal = gains.length + losses.length;
        const winRate = decisiveTotal > 0 ? ((gains.length / decisiveTotal) * 100).toFixed(1) : 0;

        const totalROI = filteredHistory.reduce((acc, s) => acc + (s.final_roi || 0), 0);

        return {
            total: filteredHistory.length,
            gains: gains.length,
            losses: losses.length,
            winRate,
            totalROI: totalROI.toFixed(2)
        };
    }, [filteredHistory]);

    const totalPages = Math.ceil(filteredHistory.length / ITEMS_PER_PAGE);
    const paginatedItems = filteredHistory.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    if (loading) return <div className="loading"><div className="spinner"></div></div>;

    return (
        <div className="signal-journey history-page">
            {/* Header with Title and Stats */}
            <div className="history-header">
                <div className="history-header-new">
                    <div className="history-title-section">
                        <div className="history-icon-wrapper">
                            <IconHistory />
                        </div>
                        <div className="history-title-text">
                            <h2>{t('signalJourney.history')}</h2>
                            <p>{t('signalJourney.last10Days')}</p>
                        </div>
                    </div>

                    <div className="history-stats-resume">
                        <div className="resume-item">
                            <span className="resume-label">Total</span>
                            <span className="resume-value">{stats.total}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item win">
                            <span className="resume-label">Wins</span>
                            <span className="resume-value">{stats.gains}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item loss">
                            <span className="resume-label">Losses</span>
                            <span className="resume-value">{stats.losses}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item highlight">
                            <span className="resume-label">Win Rate</span>
                            <span className="resume-value">{stats.winRate}%</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className={`resume-item ${parseFloat(stats.totalROI) >= 0 ? 'win' : 'loss'}`}>
                            <span className="resume-label">ROI Total</span>
                            <span className="resume-value">{parseFloat(stats.totalROI) >= 0 ? '+' : ''}{stats.totalROI}%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Controls: Search and Filters */}
            <div className="history-controls-container">
                <div className="search-wrapper">
                    <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <input
                        type="text"
                        placeholder="Buscar par (ex: BTC)..."
                        className="history-search-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value.toUpperCase())}
                    />
                    {searchTerm && (
                        <button className="clear-search" onClick={() => setSearchTerm('')}>&times;</button>
                    )}
                </div>

                <div className="history-filter-tabs">
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
                    <button
                        className={`h-tab expired ${activeFilter === 'EXPIRED' ? 'active' : ''}`}
                        onClick={() => setActiveFilter('EXPIRED')}
                    >
                        Expirados
                    </button>
                </div>
            </div>

            <div className="sj-active-section">
                {filteredHistory.length === 0 ? (
                    <div className="history-empty">
                        <div className="empty-icon-circle">
                            <IconHistory />
                        </div>
                        <h3 className="empty-title">
                            {searchTerm ? `Nenhum resultado para "${searchTerm}"` : t('signalJourney.noHistory')}
                        </h3>
                    </div>
                ) : (
                    <>
                        <div className="history-list-container">
                            {/* Mobile/Desktop Card List */}
                            <div className="history-cards-list">
                                {paginatedItems.map(signal => (
                                    <HistoryCard key={signal.id} signal={signal} t={t} />
                                ))}
                            </div>
                        </div>
                        <PaginationControls
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={setCurrentPage}
                            t={t}
                        />
                    </>
                )}
            </div>
        </div>
    );
}
