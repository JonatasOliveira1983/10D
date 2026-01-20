import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './SignalJourney.css';

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
                    {signal.llm_validation?.reasoning && (
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
    const ITEMS_PER_PAGE = 10;

    // Filter to last 10 days
    const tenDaysAgo = Date.now() - (10 * 24 * 60 * 60 * 1000);
    const filteredHistory = history
        .filter(s => s.timestamp > tenDaysAgo)
        .sort((a, b) => b.timestamp - a.timestamp);

    const totalPages = Math.ceil(filteredHistory.length / ITEMS_PER_PAGE);
    const paginatedItems = filteredHistory.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    if (loading) return <div className="loading"><div className="spinner"></div></div>;

    return (
        <div className="signal-journey history-page">
            <div className="sj-header-panel compact">
                <div className="sj-header-title">
                    <IconHistory />
                    <div className="sj-title-text">
                        <span className="sj-title-main">{t('signalJourney.history')}</span>
                        <span className="sj-title-sub">{t('signalJourney.last10Days')}</span>
                    </div>
                </div>
            </div>

            <div className="sj-active-section">
                {filteredHistory.length === 0 ? (
                    <div className="empty-state">
                        <p>{t('signalJourney.noHistory')}</p>
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
