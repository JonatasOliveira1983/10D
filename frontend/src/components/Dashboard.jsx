import React, { useState, useEffect } from 'react';
import SignalCard from './SignalCard';
import { IconHistory } from './Icons';

export default function Dashboard({ signals, pinnedSymbol, onPin, loading }) {
    const [status, setStatus] = useState(null);
    const [statusLoading, setStatusLoading] = useState(true);
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('/api/bankroll/status');
                if (res.ok) {
                    const data = await res.json();
                    setStatus(data);
                }
            } catch (e) {
                console.error('Error fetching bankroll status:', e);
            } finally {
                setStatusLoading(false);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);
    const formatCurrency = (val) => {
        const num = Number(val);
        return isNaN(num) ? '$0.00' : `$${num.toFixed(2)}`;
    };

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
                Sinais Ativos ({signals.length})
            </h2>

            {signals.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon-circle">
                        <IconHistory size={32} />
                    </div>
                    <h3 className="empty-title">Nenhum sinal ativo no momento</h3>
                    <p className="empty-text">
                        O sistema está monitorando os pares. Novos sinais aparecerão aqui quando detectados.
                    </p>
                </div>
            ) : (
                <div className="signals-grid">
                    {signals.map((signal) => (
                        <SignalCard
                            key={signal.id}
                            signal={signal}
                            isPinned={pinnedSymbol === signal.symbol}
                            onPin={() => onPin(signal.symbol)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
