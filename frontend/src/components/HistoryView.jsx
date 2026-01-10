import React from 'react';
import SignalCard from './SignalCard';

export default function HistoryView({ history, loading }) {
    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <div className="loading-text">Carregando histórico...</div>
            </div>
        );
    }

    return (
        <div className="history-view">
            <h2 className="section-title">
                📜 Histórico de Sinais ({history.length})
            </h2>

            {history.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📂</div>
                    <h3 className="empty-title">Nenhum sinal no histórico</h3>
                    <p className="empty-text">
                        Sinais finalizados aparecerão aqui.
                    </p>
                </div>
            ) : (
                <div className="signals-grid">
                    {history.map((signal) => (
                        <SignalCard key={signal.id} signal={signal} />
                    ))}
                </div>
            )}
        </div>
    );
}
