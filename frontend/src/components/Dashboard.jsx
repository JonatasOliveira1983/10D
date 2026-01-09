import React from 'react';
import SignalCard from './SignalCard';

export default function Dashboard({ signals, loading }) {
    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <div className="loading-text">Carregando sinais...</div>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <h2 className="section-title">
                🚨 Sinais Ativos ({signals.length})
            </h2>

            {signals.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📭</div>
                    <h3 className="empty-title">Nenhum sinal ativo no momento</h3>
                    <p className="empty-text">
                        O sistema está monitorando os pares. Novos sinais aparecerão aqui quando detectados.
                    </p>
                </div>
            ) : (
                <div className="signals-grid">
                    {signals.map((signal) => (
                        <SignalCard key={signal.id} signal={signal} />
                    ))}
                </div>
            )}
        </div>
    );
}
