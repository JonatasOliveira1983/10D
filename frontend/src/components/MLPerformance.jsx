import React, { useState, useEffect } from 'react';
import { IconAI } from './Icons';
import './AIAnalytics.css'; // Reusing existing styles

export default function MLPerformance() {
    const [mlStatus, setMlStatus] = useState(null);
    const [mlMetrics, setMlMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchMLData = async () => {
        try {
            const [statusRes, metricsRes] = await Promise.all([
                fetch('/api/ml/status').then(r => r.json()),
                fetch('/api/ml/metrics').then(r => r.json()).catch(() => null)
            ]);
            setMlStatus(statusRes);
            setMlMetrics(metricsRes);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching ML data:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMLData();
        // Update every 15 seconds to show real-time training status
        const interval = setInterval(fetchMLData, 15000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="loading-state">Carregando ML Performance...</div>;

    const isReady = mlStatus?.model_loaded && mlMetrics?.status === 'SUCCESS';
    const accuracy = mlMetrics?.metrics?.accuracy || 0;
    const precision = mlMetrics?.metrics?.precision || 0;
    const recall = mlMetrics?.metrics?.recall || 0;
    const f1 = mlMetrics?.metrics?.f1_score || 0;

    // Confusion Matrix
    const cm = mlMetrics?.confusion_matrix || { true_positive: 0, false_positive: 0, true_negative: 0, false_negative: 0 };
    const total = cm.true_positive + cm.false_positive + cm.true_negative + cm.false_negative;

    // Feature Importance
    const featureImportance = mlMetrics?.feature_importance || {};
    const topFeatures = Object.entries(featureImportance)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8);

    const getMetricColor = (value) => {
        if (value >= 0.75) return '#00e676';
        if (value >= 0.60) return '#ffd700';
        return '#ff5252';
    };

    const featureLabels = {
        'oi_change_pct': 'OI Change %',
        'lsr_change_pct': 'LSR Change %',
        'cvd_delta': 'CVD Delta',
        'rs_score': 'RS Score',
        'volatility_idx': 'Volatility Index',
        'master_score': 'Master Score',
        'trend_aligned': 'Trend Aligned',
        'rsi_value': 'RSI Value'
    };

    return (
        <div className="ai-analytics-page">
            <div className="analytics-header">
                <div className="header-content">
                    <h1><IconAI size={28} /> ML Performance</h1>
                    <p>Machine Learning Predictor - Random Forest Classifier</p>
                </div>
                <div className="header-badge">
                    <span className="badge-label">Status</span>
                    <span className={`badge-value ${isReady ? 'active' : 'pending'}`}>
                        {isReady ? 'Treinado' : 'Não Treinado'}
                    </span>
                </div>
            </div>

            <div className="analytics-grid">
                {/* Auto-Training Status Card */}
                <div className="analytics-card progress-card glass">
                    <div className="card-header">
                        <h3>🤖 Auto-Training</h3>
                        <span className={`card-tag ${mlStatus?.is_training ? 'training' : mlStatus?.model_loaded ? 'active' : 'pending'}`}>
                            {mlStatus?.is_training ? 'Treinando...' : mlStatus?.model_loaded ? 'Ativo' : 'Aguardando'}
                        </span>
                    </div>

                    {/* Training Progress */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.85rem', opacity: 0.7 }}>
                                {mlStatus?.model_loaded ? 'Próximo retreino' : 'Primeiro treino'}
                            </span>
                            <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>
                                {mlStatus?.model_loaded
                                    ? `${mlStatus?.samples_since_last_train || 0}/${mlStatus?.auto_train_interval || 30} amostras`
                                    : `${mlStatus?.available_samples || 0}/${mlStatus?.min_samples_required || 100} amostras`
                                }
                            </span>
                        </div>
                        <div style={{
                            height: '8px',
                            background: 'rgba(255,255,255,0.1)',
                            borderRadius: '4px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                height: '100%',
                                width: `${mlStatus?.training_progress_pct || 0}%`,
                                background: mlStatus?.is_training
                                    ? 'linear-gradient(90deg, #667eea, #764ba2)'
                                    : 'linear-gradient(90deg, #00d4aa, #00e676)',
                                borderRadius: '4px',
                                transition: 'width 0.5s ease',
                                animation: mlStatus?.is_training ? 'pulse 1.5s ease-in-out infinite' : 'none'
                            }} />
                        </div>
                        {mlStatus?.is_training && (
                            <div style={{
                                marginTop: '0.5rem',
                                fontSize: '0.8rem',
                                color: '#667eea',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                <span className="spinner-small" />
                                Retreinando modelo automaticamente...
                            </div>
                        )}
                    </div>

                    <div className="feature-list">
                        <div className="feature-item">
                            <span className="feature-label">Modelo Carregado</span>
                            <span className={`feature-value-inline ${mlStatus?.model_loaded ? 'success' : 'danger'}`}>
                                {mlStatus?.model_loaded ? '✓ Sim' : '✗ Não'}
                            </span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-label">Total de Amostras</span>
                            <span className="feature-value-inline">{mlStatus?.available_samples || 0}</span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-label">Último Treinamento</span>
                            <span className="feature-value-inline">
                                {mlStatus?.last_training || 'Nunca'}
                            </span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-label">Accuracy Atual</span>
                            <span className="feature-value-inline" style={{ color: getMetricColor(mlStatus?.last_accuracy || 0) }}>
                                {mlStatus?.last_accuracy ? `${(mlStatus.last_accuracy * 100).toFixed(1)}%` : 'N/A'}
                            </span>
                        </div>
                        <div className="feature-item">
                            <span className="feature-label">Intervalo de Retreino</span>
                            <span className="feature-value-inline">
                                A cada {mlStatus?.auto_train_interval || 30} amostras
                            </span>
                        </div>
                    </div>
                </div>

                {/* Metrics Overview */}
                {isReady && (
                    <>
                        <div className="analytics-card accuracy-card glass">
                            <div className="card-header">
                                <h3>Accuracy</h3>
                                <span className="card-tag">Métrica Principal</span>
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
                                        stroke={getMetricColor(accuracy)}
                                        strokeWidth="8"
                                        strokeLinecap="round"
                                        strokeDasharray={`${accuracy * 126} 126`}
                                        className="gauge-fill"
                                    />
                                </svg>
                                <div className="gauge-value" style={{ color: getMetricColor(accuracy) }}>
                                    {(accuracy * 100).toFixed(1)}%
                                </div>
                            </div>
                            <p className="gauge-label">
                                {mlMetrics.samples.test} amostras de teste
                            </p>
                        </div>

                        <div className="analytics-card score-comparison-card glass">
                            <div className="card-header">
                                <h3>Métricas de Performance</h3>
                                <span className="card-tag">Classificação</span>
                            </div>
                            <div className="score-compare" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
                                <div className="score-box">
                                    <span className="score-label">Precision</span>
                                    <span className="score-value" style={{ color: getMetricColor(precision) }}>
                                        {(precision * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="score-box">
                                    <span className="score-label">Recall</span>
                                    <span className="score-value" style={{ color: getMetricColor(recall) }}>
                                        {(recall * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="score-box">
                                    <span className="score-label">F1-Score</span>
                                    <span className="score-value" style={{ color: getMetricColor(f1) }}>
                                        {(f1 * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Confusion Matrix */}
                        <div className="analytics-card glass" style={{ gridColumn: 'span 2' }}>
                            <div className="card-header">
                                <h3>Confusion Matrix</h3>
                                <span className="card-tag">Análise de Erros</span>
                            </div>
                            <div style={{ padding: '1rem' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', maxWidth: '400px', margin: '0 auto' }}>
                                    <div style={{ background: 'rgba(0, 230, 118, 0.1)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center', border: '2px solid rgba(0, 230, 118, 0.3)' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00e676' }}>
                                            {cm.true_positive}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '0.5rem' }}>
                                            True Positive
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                            {total > 0 ? ((cm.true_positive / total) * 100).toFixed(1) : 0}%
                                        </div>
                                    </div>
                                    <div style={{ background: 'rgba(255, 82, 82, 0.1)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center', border: '2px solid rgba(255, 82, 82, 0.3)' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ff5252' }}>
                                            {cm.false_positive}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '0.5rem' }}>
                                            False Positive
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                            {total > 0 ? ((cm.false_positive / total) * 100).toFixed(1) : 0}%
                                        </div>
                                    </div>
                                    <div style={{ background: 'rgba(255, 82, 82, 0.1)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center', border: '2px solid rgba(255, 82, 82, 0.3)' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ff5252' }}>
                                            {cm.false_negative}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '0.5rem' }}>
                                            False Negative
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                            {total > 0 ? ((cm.false_negative / total) * 100).toFixed(1) : 0}%
                                        </div>
                                    </div>
                                    <div style={{ background: 'rgba(0, 230, 118, 0.1)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center', border: '2px solid rgba(0, 230, 118, 0.3)' }}>
                                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00e676' }}>
                                            {cm.true_negative}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '0.5rem' }}>
                                            True Negative
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                            {total > 0 ? ((cm.true_negative / total) * 100).toFixed(1) : 0}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Feature Importance */}
                        <div className="analytics-card type-performance-card glass" style={{ gridColumn: 'span 2' }}>
                            <div className="card-header">
                                <h3>Feature Importance</h3>
                                <span className="card-tag premium">Random Forest</span>
                            </div>
                            <div className="type-bars">
                                {topFeatures.map(([feature, importance]) => (
                                    <div key={feature} className="type-bar-item">
                                        <div className="type-bar-header">
                                            <span className="type-name">{featureLabels[feature] || feature}</span>
                                            <span className="type-stats">
                                                <span className="type-rate" style={{ color: '#667eea' }}>
                                                    {(importance * 100).toFixed(1)}%
                                                </span>
                                            </span>
                                        </div>
                                        <div className="type-bar-wrapper">
                                            <div
                                                className="type-bar-fill"
                                                style={{
                                                    width: `${importance * 100}%`,
                                                    background: 'linear-gradient(90deg, rgba(102, 126, 234, 0.4), rgba(102, 126, 234, 1))'
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Training Info */}
                        <div className="analytics-card feature-card glass" style={{ gridColumn: 'span 2' }}>
                            <div className="card-header">
                                <h3>Informações de Treinamento</h3>
                                <span className="card-tag">Dataset</span>
                            </div>
                            <div className="feature-list">
                                <div className="feature-item">
                                    <span className="feature-label">Total de Amostras</span>
                                    <span className="feature-value-inline">{mlMetrics.samples.total}</span>
                                </div>
                                <div className="feature-item">
                                    <span className="feature-label">Amostras de Treino</span>
                                    <span className="feature-value-inline success">{mlMetrics.samples.train}</span>
                                </div>
                                <div className="feature-item">
                                    <span className="feature-label">Amostras de Teste</span>
                                    <span className="feature-value-inline">{mlMetrics.samples.test}</span>
                                </div>
                                <div className="feature-item">
                                    <span className="feature-label">Wins no Dataset</span>
                                    <span className="feature-value-inline success">{mlMetrics.samples.wins}</span>
                                </div>
                                <div className="feature-item">
                                    <span className="feature-label">Losses no Dataset</span>
                                    <span className="feature-value-inline danger">{mlMetrics.samples.losses}</span>
                                </div>
                                <div className="feature-item">
                                    <span className="feature-label">Win Rate do Dataset</span>
                                    <span className="feature-value-inline">
                                        {((mlMetrics.samples.wins / (mlMetrics.samples.wins + mlMetrics.samples.losses)) * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {!isReady && (
                    <div className="analytics-card glass" style={{ gridColumn: 'span 2', textAlign: 'center', padding: '3rem' }}>
                        <IconAI size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                        <h3>Modelo Não Treinado</h3>
                        <p style={{ opacity: 0.7, marginTop: '0.5rem' }}>
                            {mlStatus?.available_samples < 100
                                ? `Coletando dados... ${mlStatus?.available_samples}/100 amostras`
                                : 'Clique em "Treinar Modelo" para começar'}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
