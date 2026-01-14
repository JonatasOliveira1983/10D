import React, { useState, useEffect } from 'react';
import { IconAI, IconHistory } from './Icons';
import './AIAnalytics.css';

export default function AIAnalytics() {
    const [progress, setProgress] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [brain, setBrain] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAIData = async () => {
            try {
                const [progRes, analRes, brainRes] = await Promise.all([
                    fetch('/api/ai/progress').then(r => r.json()),
                    fetch('/api/ai/analytics').then(r => r.json()),
                    fetch('/api/ai/brain').then(r => r.json())
                ]);
                setProgress(progRes);
                setAnalytics(analRes);
                setBrain(brainRes);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching AI data:', error);
                setLoading(false);
            }
        };

        fetchAIData();
        const interval = setInterval(fetchAIData, 30000);
        return () => clearInterval(interval);
    }, []);

    // Animated number component
    const AnimatedNumber = ({ value, suffix = '', decimals = 0 }) => {
        const [display, setDisplay] = useState(0);
        useEffect(() => {
            const target = parseFloat(value) || 0;
            const duration = 1000;
            const steps = 30;
            const increment = target / steps;
            let current = 0;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    setDisplay(target);
                    clearInterval(timer);
                } else {
                    setDisplay(current);
                }
            }, duration / steps);
            return () => clearInterval(timer);
        }, [value]);
        return <>{display.toFixed(decimals)}{suffix}</>;
    };

    // Win rate color based on value
    const getWinRateColor = (rate) => {
        if (rate >= 70) return '#00e676';
        if (rate >= 50) return '#ffd700';
        return '#ff5252';
    };

    // Signal type labels
    const typeLabels = {
        'EMA_CROSSOVER': 'EMA Crossover',
        'TREND_PULLBACK': 'Trend Pullback',
        'RSI_BB_REVERSAL': 'RSI + Bollinger',
        'JUDAS_SWING': 'Judas Swing'
    };

    if (loading) return <div className="loading-state">Carregando Auditoria de IA...</div>;

    const winRate = analytics?.status === 'READY' ? analytics.data.win_rate : 0;
    const performanceByType = analytics?.status === 'READY' ? analytics.data.performance_by_type : {};
    const totalSamples = progress?.current_samples || 0;
    const tradeSamples = analytics?.status === 'READY' ? analytics.data.total_samples : 0;
    const expiredCount = totalSamples - tradeSamples;

    return (
        <div className="ai-analytics-page">
            <div className="analytics-header">
                <div className="header-content">
                    <h1><IconAI size={28} /> Auditoria de IA</h1>
                    <p>Camada de Validação Estatística & Machine Learning</p>
                </div>
                <div className="header-badge">
                    <span className="badge-label">Status</span>
                    <span className={`badge-value ${brain?.status === 'READY' ? 'active' : 'pending'}`}>
                        {brain?.status === 'READY' ? 'ML Ativo' : 'Coletando'}
                    </span>
                </div>
            </div>

            <div className="analytics-grid">
                {/* Data Collection Progress */}
                <div className="analytics-card progress-card glass">
                    <div className="card-header">
                        <h3>Coleta de Dados</h3>
                        <span className="card-tag">Data Logger</span>
                    </div>
                    <div className="progress-container">
                        <div className="progress-bar-wrapper">
                            <div
                                className="progress-bar-fill"
                                style={{ width: `${progress?.progress_pct || 0}%` }}
                            ></div>
                        </div>
                        <div className="progress-stats">
                            <span>{totalSamples} / {progress?.target_samples || 300}</span>
                            <span className="progress-pct">{progress?.progress_pct?.toFixed(1) || 0}%</span>
                        </div>
                    </div>
                    <div className="progress-breakdown">
                        <div className="breakdown-item">
                            <span className="breakdown-label">Trades (TP/SL)</span>
                            <span className="breakdown-value success">{tradeSamples}</span>
                        </div>
                        <div className="breakdown-item">
                            <span className="breakdown-label">Expirados</span>
                            <span className="breakdown-value muted">{expiredCount}</span>
                        </div>
                    </div>
                </div>

                {/* Win Rate Gauge */}
                <div className="analytics-card accuracy-card glass">
                    <div className="card-header">
                        <h3>Taxa de Acerto</h3>
                        <span className="card-tag">Performance</span>
                    </div>
                    <div className="gauge-container">
                        <svg viewBox="0 0 100 60" className="gauge-svg">
                            <path
                                d="M 10 50 A 40 40 0 0 1 90 50"
                                fill="none"
                                stroke="rgba(255,255,255,0.08)"
                                strokeWidth="8"
                                strokeLinecap="round"
                            />
                            <path
                                d="M 10 50 A 40 40 0 0 1 90 50"
                                fill="none"
                                stroke={getWinRateColor(winRate)}
                                strokeWidth="8"
                                strokeLinecap="round"
                                strokeDasharray={`${(winRate / 100) * 126} 126`}
                                className="gauge-fill"
                            />
                        </svg>
                        <div className="gauge-value" style={{ color: getWinRateColor(winRate) }}>
                            <AnimatedNumber value={winRate} suffix="%" decimals={1} />
                        </div>
                    </div>
                    <p className="gauge-label">
                        {analytics?.status === 'READY'
                            ? `Baseado em ${tradeSamples} trades finalizados`
                            : 'Aguardando dados suficientes'}
                    </p>
                </div>

                {/* Performance by Signal Type */}
                <div className="analytics-card type-performance-card glass">
                    <div className="card-header">
                        <h3>Performance por Estratégia</h3>
                        <span className="card-tag">Breakdown</span>
                    </div>
                    {analytics?.status === 'READY' && Object.keys(performanceByType).length > 0 ? (
                        <div className="type-bars">
                            {Object.entries(performanceByType)
                                .sort((a, b) => b[1].win_rate - a[1].win_rate)
                                .map(([type, data]) => (
                                    <div key={type} className="type-bar-item">
                                        <div className="type-bar-header">
                                            <span className="type-name">{typeLabels[type] || type}</span>
                                            <span className="type-stats">
                                                <span className="type-rate" style={{ color: getWinRateColor(data.win_rate) }}>
                                                    {data.win_rate}%
                                                </span>
                                                <span className="type-count">{data.count} trades</span>
                                            </span>
                                        </div>
                                        <div className="type-bar-wrapper">
                                            <div
                                                className="type-bar-fill"
                                                style={{
                                                    width: `${data.win_rate}%`,
                                                    background: `linear-gradient(90deg, ${getWinRateColor(data.win_rate)}40, ${getWinRateColor(data.win_rate)})`
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>Aguardando trades finalizados para análise</p>
                        </div>
                    )}
                </div>

                {/* Score Comparison */}
                <div className="analytics-card score-comparison-card glass">
                    <div className="card-header">
                        <h3>Score Médio</h3>
                        <span className="card-tag">Análise Comparativa</span>
                    </div>
                    {analytics?.status === 'READY' ? (
                        <div className="score-compare">
                            <div className="score-box wins">
                                <span className="score-label">Ganhos</span>
                                <span className="score-value">
                                    <AnimatedNumber
                                        value={analytics.data.avg_master_score_wins}
                                        decimals={1}
                                    />
                                </span>
                            </div>
                            <div className="score-divider">
                                <div className="divider-line"></div>
                                <span>VS</span>
                                <div className="divider-line"></div>
                            </div>
                            <div className="score-box losses">
                                <span className="score-label">Perdas</span>
                                <span className="score-value">
                                    <AnimatedNumber
                                        value={analytics.data.avg_master_score_losses}
                                        decimals={1}
                                    />
                                </span>
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state">Analisando scores...</div>
                    )}
                </div>

                {/* ML Brain Insights */}
                {brain?.status === 'READY' && (
                    <div className="analytics-card brain-card glass">
                        <div className="card-header">
                            <h3>ML Brain Insights</h3>
                            <span className="card-tag premium">Machine Learning</span>
                        </div>
                        <div className="brain-content">
                            <div className="brain-thresholds">
                                <div className="threshold-item">
                                    <span className="threshold-label">Score Mínimo Sugerido</span>
                                    <span className="threshold-value">
                                        {brain.data.optimal_thresholds?.min_master_score?.toFixed(1) || '--'}
                                    </span>
                                </div>
                                <div className="threshold-item">
                                    <span className="threshold-label">RSI Ideal</span>
                                    <span className="threshold-value">
                                        {brain.data.optimal_thresholds?.optimal_rsi_range
                                            ? `${brain.data.optimal_thresholds.optimal_rsi_range[0].toFixed(0)} - ${brain.data.optimal_thresholds.optimal_rsi_range[1].toFixed(0)}`
                                            : '--'}
                                    </span>
                                </div>
                            </div>
                            <div className="brain-features">
                                <h4>Feature Importance</h4>
                                {Object.entries(brain.data.feature_importance || {})
                                    .sort((a, b) => b[1] - a[1])
                                    .slice(0, 5)
                                    .map(([feature, importance]) => (
                                        <div key={feature} className="feature-bar-item">
                                            <span className="feature-name">{feature.replace(/_/g, ' ')}</span>
                                            <div className="feature-bar-wrapper">
                                                <div
                                                    className="feature-bar-fill"
                                                    style={{ width: `${importance * 100}%` }}
                                                ></div>
                                            </div>
                                            <span className="feature-value">{(importance * 100).toFixed(0)}%</span>
                                        </div>
                                    ))}
                            </div>
                            <div className="brain-meta">
                                <span>Último treino: {brain.data.last_training
                                    ? new Date(brain.data.last_training).toLocaleDateString('pt-BR')
                                    : 'N/A'}</span>
                                <span>{brain.data.samples_analyzed || 0} amostras processadas</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* OI Impact */}
                <div className="analytics-card feature-card glass">
                    <div className="card-header">
                        <h3>Impacto Open Interest</h3>
                        <span className="card-tag">Derivativos</span>
                    </div>
                    {analytics?.status === 'READY' ? (
                        <div className="feature-list">
                            <div className="feature-item">
                                <span className="feature-label">Δ% Médio OI em Ganhos</span>
                                <span className="feature-value-inline success">{analytics.data.oi_impact.avg_oi_change_wins}%</span>
                            </div>
                            <div className="feature-item">
                                <span className="feature-label">Δ% Médio OI em Perdas</span>
                                <span className="feature-value-inline danger">{analytics.data.oi_impact.avg_oi_change_losses}%</span>
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>Aguardando amostras</p>
                        </div>
                    )}
                </div>

                {/* Best Edge */}
                <div className="analytics-card edge-card glass">
                    <div className="card-header">
                        <h3>Melhor Vantagem</h3>
                        <span className="card-tag highlight">Edge</span>
                    </div>
                    {analytics?.status === 'READY' ? (
                        <div className="edge-content">
                            <div className="edge-type">{typeLabels[analytics.data.best_edge.type] || analytics.data.best_edge.type}</div>
                            <div className="edge-rate">{analytics.data.best_edge.win_rate}%</div>
                            <div className="edge-label">Win Rate</div>
                        </div>
                    ) : (
                        <div className="empty-state">Analisando padrões...</div>
                    )}
                </div>
            </div>

            <div className="ai-notice glass">
                <div className="notice-icon">
                    <IconHistory size={20} />
                </div>
                <div className="notice-content">
                    <strong>ML Brain Ativo</strong>
                    <p>
                        O sistema está ajustando scores dinamicamente. Sinais com RSI fora do range ótimo
                        ({brain?.data?.optimal_thresholds?.optimal_rsi_range?.[0]?.toFixed(0) || 45} - {brain?.data?.optimal_thresholds?.optimal_rsi_range?.[1]?.toFixed(0) || 64})
                        recebem penalidade. RSI ideal adiciona bônus ao score final.
                    </p>
                </div>
            </div>
        </div>
    );
}
