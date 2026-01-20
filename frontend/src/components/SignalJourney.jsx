import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchSentiment } from '../services/api';
import './SignalJourney.css';

// SVG Logo for Signal Journey
const SignalJourneyLogo = () => (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="journeyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00d4aa" />
                <stop offset="100%" stopColor="#7c3aed" />
            </linearGradient>
        </defs>
        <circle cx="16" cy="16" r="15" stroke="url(#journeyGrad)" strokeWidth="2" fill="none" />
        <path d="M8 20L12 14L16 17L20 10L24 12" stroke="url(#journeyGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="16" cy="16" r="3" fill="url(#journeyGrad)" />
    </svg>
);

// Icon components for cleaner UI
const IconWinRate = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2L12.5 7.5L18 8.5L14 12.5L15 18L10 15L5 18L6 12.5L2 8.5L7.5 7.5L10 2Z"
            fill="currentColor" opacity="0.2" stroke="currentColor" strokeWidth="1.5" />
    </svg>
);

const IconROI = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M2 15L6 10L10 12L14 6L18 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="18" cy="8" r="2" fill="currentColor" />
    </svg>
);

const IconAI = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.1" />
        <circle cx="10" cy="10" r="3" fill="currentColor" />
        <path d="M10 2V5M10 15V18M2 10H5M15 10H18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
);

const IconTrophy = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M6 3H14V8C14 10.2091 12.2091 12 10 12C7.79086 12 6 10.2091 6 8V3Z" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="1.5" />
        <path d="M6 5H4C3 5 2 6 2 7C2 8 3 9 4 9H6" stroke="currentColor" strokeWidth="1.5" />
        <path d="M14 5H16C17 5 18 6 18 7C18 8 17 9 16 9H14" stroke="currentColor" strokeWidth="1.5" />
        <path d="M8 12V14H12V12" stroke="currentColor" strokeWidth="1.5" />
        <path d="M6 17H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);

const IconSignal = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="2" fill="currentColor" />
        <circle cx="10" cy="10" r="5" stroke="currentColor" strokeWidth="1.5" fill="none" opacity="0.5" />
        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" fill="none" opacity="0.3" />
    </svg>
);

const SentimentWidget = ({ sentiment, t }) => {
    if (!sentiment) return null;

    const { score, sentiment: label, summary } = sentiment;

    let color = 'var(--text-muted)';
    if (score >= 55) color = 'var(--long-color)';
    if (score <= 45) color = 'var(--short-color)';

    return (
        <div className="sentiment-bar">
            <div className="sentiment-top">
                <div className="sentiment-main">
                    <span className="sentiment-tag" style={{ backgroundColor: `${color}22`, color }}>
                        {label}
                    </span>
                    <span className="sentiment-index">Fear & Greed Index: <strong>{score}</strong></span>
                </div>
                <div className="sentiment-gauge">
                    <div className="gauge-track">
                        <div className="gauge-fill" style={{ width: `${score}%`, backgroundColor: color }} />
                    </div>
                </div>
            </div>
            {summary && (
                <div className="sentiment-insight">
                    <p>"{summary}"</p>
                </div>
            )}
        </div>
    );
};

// Sparkline component for mini charts
const Sparkline = ({ data, color = '#00d4aa', width = 60, height = 24 }) => {
    if (!data || data.length < 2) return null;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((val - min) / range) * (height - 4) - 2;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg width={width} height={height} className="sparkline">
            <defs>
                <linearGradient id={`spark-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={color} />
                </linearGradient>
            </defs>
            <polyline
                fill="none"
                stroke={`url(#spark-${color})`}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={points}
            />
        </svg>
    );
};

// LLM Header Panel with metrics and sparklines
const LLMHeaderPanel = ({ summary, loading, t }) => {
    const metrics = [
        {
            icon: <IconWinRate />,
            label: t('signalJourney.winRate'),
            value: `${summary?.win_rate?.toFixed(1) || 0}%`,
            sparkData: summary?.win_rate_history || [],
            color: '#00d4aa'
        },
        {
            icon: <IconROI />,
            label: t('signalJourney.roiAccum'),
            value: `${summary?.roi_accumulated >= 0 ? '+' : ''}${summary?.roi_accumulated?.toFixed(1) || 0}%`,
            sparkData: summary?.roi_history || [],
            color: '#00d4ff'
        },
        {
            icon: <IconAI />,
            label: t('signalJourney.llmConf'),
            value: `${summary?.llm_confidence_avg?.toFixed(0) || 0}%`,
            isProgress: true,
            progress: summary?.llm_confidence_avg || 0,
            color: '#7c3aed'
        },
        {
            icon: <IconTrophy />,
            label: t('signalJourney.bestCatch'),
            value: summary?.best_catch ? `+${summary.best_catch.roi?.toFixed(1)}%` : '--',
            subtext: summary?.best_catch?.symbol || '',
            color: '#ff9f43'
        },
        {
            icon: <IconSignal />,
            label: t('signalJourney.active'),
            value: summary?.active_signals || 0,
            isCount: true,
            color: '#ef4444'
        }
    ];

    return (
        <div className="sj-header-panel">
            <div className="sj-header-title">
                <SignalJourneyLogo />
                <div className="sj-title-text">
                    <span className="sj-title-main">Signal Journey</span>
                    <span className="sj-title-sub">{t('signalJourney.title')}</span>
                </div>
            </div>
            <div className="sj-metrics-grid">
                {metrics.map((metric, idx) => (
                    <div key={idx} className="sj-metric-card">
                        <div className="metric-icon" style={{ color: metric.color }}>
                            {metric.icon}
                        </div>
                        <div className="metric-content">
                            <div className="metric-label">{metric.label}</div>
                            <div className="metric-value" style={{ color: metric.color }}>
                                {metric.value}
                            </div>
                        </div>
                        <div className="metric-visual">
                            {metric.sparkData && metric.sparkData.length > 0 && (
                                <Sparkline data={metric.sparkData} color={metric.color} />
                            )}
                            {metric.isProgress && (
                                <div className="metric-progress-bar">
                                    <div
                                        className="metric-progress-fill"
                                        style={{
                                            width: `${metric.progress}%`,
                                            background: `linear-gradient(90deg, ${metric.color}33, ${metric.color})`
                                        }}
                                    />
                                </div>
                            )}
                            {metric.subtext && (
                                <div className="metric-subtext">{metric.subtext}</div>
                            )}
                            {metric.isCount && (
                                <div className="metric-dots">
                                    {[...Array(Math.min(metric.value, 5))].map((_, i) => (
                                        <span key={i} className="dot active" style={{ background: metric.color }} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// Signal Progress Bar component
const SignalProgressBar = ({ signal, t }) => {
    const { symbol, direction, entry_price, take_profit, stop_loss, current_roi,
        highest_roi, llm_validation, trailing_stop_active, partial_tp_hit, timestamp } = signal;

    const roi = current_roi || 0;
    const tp_pct = signal.dynamic_targets?.tp_pct || 2;
    const sl_pct = signal.dynamic_targets?.sl_pct || 1;

    // Calculate position on progress bar (-SL to +TP)
    const totalRange = sl_pct + tp_pct;
    const currentPos = ((roi + sl_pct) / totalRange) * 100;
    const clampedPos = Math.max(0, Math.min(100, currentPos));

    // Time active
    const minutesActive = Math.floor((Date.now() - timestamp) / 60000);
    const timeStr = minutesActive < 60
        ? `${minutesActive}m`
        : `${Math.floor(minutesActive / 60)}h ${minutesActive % 60}m`;

    const llmConf = llm_validation?.confidence || 0;

    return (
        <div className={`sj-signal-card ${direction.toLowerCase()}`}>
            <div className="signal-header">
                <div className="signal-info">
                    <span className={`direction-indicator ${direction.toLowerCase()}`} />
                    <span className="signal-symbol">{symbol}</span>
                    <span className={`direction-tag ${direction.toLowerCase()}`}>
                        {direction}
                    </span>
                </div>
                <div className="signal-metrics">
                    {llmConf > 0 && (
                        <span className="ai-badge" title="LLM Confidence">
                            <IconAI /> {(llmConf * 100).toFixed(0)}%
                        </span>
                    )}
                    <span className={`roi-display ${roi >= 0 ? 'positive' : 'negative'}`}>
                        {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                    </span>
                </div>
            </div>

            <div className="progress-section">
                <div className="progress-labels">
                    <span className="label-sl">SL -{sl_pct}%</span>
                    <span className="label-entry">{t('signalJourney.entry')}</span>
                    <span className="label-tp">TP +{tp_pct}%</span>
                </div>
                <div className="progress-track-container">
                    <div className="progress-track">
                        <div className="entry-line" style={{ left: `${(sl_pct / totalRange) * 100}%` }} />
                        <div
                            className={`progress-fill ${roi >= 0 ? 'positive' : 'negative'}`}
                            style={{
                                left: `${(sl_pct / totalRange) * 100}%`,
                                width: `${Math.abs(roi / totalRange) * 100}%`,
                                transform: roi < 0 ? 'translateX(-100%)' : 'none'
                            }}
                        />
                        <div
                            className="position-marker"
                            style={{ left: `${clampedPos}%` }}
                        />
                    </div>
                </div>
                <div className="progress-prices">
                    <span>${stop_loss?.toFixed(2)}</span>
                    <span>${entry_price?.toFixed(2)}</span>
                    <span>${take_profit?.toFixed(2)}</span>
                </div>
            </div>

            <div className="signal-tags">
                {trailing_stop_active && (
                    <span className="tag trailing">{t('signalJourney.trailing')}</span>
                )}
                {partial_tp_hit && (
                    <span className="tag partial">{t('signalJourney.partial')}</span>
                )}
                <span className="tag time">{timeStr}</span>
                {highest_roi > 0 && (
                    <span className="tag highest">{t('signalJourney.max')}: +{highest_roi.toFixed(1)}%</span>
                )}
            </div>
        </div>
    );
};

// Pagination Controls Component (Reusable)
const PaginationControls = ({ currentPage, totalPages, onPageChange, t }) => {
    if (totalPages <= 1) return null;

    return (
        <div className="sj-pagination">
            <button
                className="pagination-btn"
                disabled={currentPage === 1}
                onClick={() => onPageChange(currentPage - 1)}
            >
                ← {t('signalJourney.prev')}
            </button>
            <span className="pagination-info">
                {currentPage} / {totalPages}
            </span>
            <button
                className="pagination-btn"
                disabled={currentPage === totalPages}
                onClick={() => onPageChange(currentPage + 1)}
            >
                {t('signalJourney.next')} →
            </button>
        </div>
    );
};

// Main Signal Journey Component
export default function SignalJourney({ signals, history, loading }) {
    const { t } = useTranslation();
    const [llmSummary, setLlmSummary] = useState(null);
    const [sentiment, setSentiment] = useState(null);
    const [activePage, setActivePage] = useState(1);
    const SIGNALS_PER_PAGE = 5;

    // Fetch LLM summary and Sentiment
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch LLM Summary
                const sumRes = await fetch('/api/llm/summary');
                if (sumRes.ok) setLlmSummary(await sumRes.json());

                // Fetch Sentiment
                const sentRes = await fetchSentiment();
                if (sentRes && sentRes.analysis) setSentiment(sentRes.analysis);
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000);

        return () => clearInterval(interval);
    }, []);

    // Calculate summary from available data if API not ready
    const computedSummary = llmSummary || (() => {
        const wins = history.filter(s => s.status === 'TP_HIT').length;
        const total = history.filter(s => s.status === 'TP_HIT' || s.status === 'SL_HIT').length;
        const avgRoi = history.reduce((sum, s) => sum + (s.final_roi || s.current_roi || 0), 0) / (history.length || 1);

        return {
            win_rate: total > 0 ? (wins / total) * 100 : 0,
            roi_accumulated: avgRoi * history.length,
            llm_confidence_avg: 70,
            active_signals: signals.length,
            best_catch: history.reduce((best, s) => {
                const roi = s.final_roi || s.current_roi || 0;
                return roi > (best?.roi || 0) ? { symbol: s.symbol, roi } : best;
            }, null)
        };
    })();

    // Pagination Logic for Active Signals
    const totalActivePages = Math.ceil(signals.length / SIGNALS_PER_PAGE);
    const paginatedSignals = signals.slice(
        (activePage - 1) * SIGNALS_PER_PAGE,
        activePage * SIGNALS_PER_PAGE
    );

    // Reset page if signals change and current page becomes empty
    useEffect(() => {
        if (activePage > totalActivePages && totalActivePages > 0) {
            setActivePage(totalActivePages);
        }
    }, [signals.length, totalActivePages, activePage]);

    return (
        <div className="signal-journey">
            <LLMHeaderPanel summary={computedSummary} loading={loading} t={t} />

            {sentiment && <SentimentWidget sentiment={sentiment} t={t} />}

            <div className="sj-active-section">
                <div className="sj-section-header">
                    <div className="section-title-group">
                        <IconSignal />
                        <h3>{t('signalJourney.activeSignals')}</h3>
                    </div>
                    {signals.length > 0 && (
                        <span className="section-badge">{signals.length} {t('signalJourney.active')}</span>
                    )}
                </div>
                {signals.length === 0 ? (
                    <div className="empty-state">
                        <IconSignal />
                        <p>{t('signalJourney.noSignals')}</p>
                    </div>
                ) : (
                    <>
                        <div className="signals-list">
                            {paginatedSignals.map(signal => (
                                <SignalProgressBar key={signal.id} signal={signal} t={t} />
                            ))}
                        </div>
                        <PaginationControls
                            currentPage={activePage}
                            totalPages={totalActivePages}
                            onPageChange={setActivePage}
                            t={t}
                        />
                    </>
                )}
            </div>
        </div>
    );
};
