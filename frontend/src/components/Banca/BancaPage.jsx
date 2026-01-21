
import React, { useState, useEffect } from 'react';
import './BancaPage.css';
import BancaLogo from './BancaLogo';

const BancaPage = () => {
    const [status, setStatus] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [statusRes, tradesRes] = await Promise.all([
                fetch('/api/bankroll/status'),
                fetch('/api/bankroll/trades')
            ]);

            if (statusRes.ok) {
                const sData = await statusRes.json();
                setStatus(sData);
            }
            if (tradesRes.ok) {
                const tData = await tradesRes.json();
                setTrades(tData);
            }
        } catch (error) {
            console.error("Error fetching bankroll data:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !status) return <div className="banca-loading">Carregando Banca...</div>;

    const currentBalance = status?.current_balance || 20.0;
    const initialBalance = status?.initial_balance || 20.0;
    const progress = status?.trade_count_cycle || 0;
    const activeSlots = status?.active_slots_used || 0;

    // Calculate stats
    const totalPnL = currentBalance - initialBalance;
    const pnlPercent = (totalPnL / initialBalance) * 100;
    const nextEntry = currentBalance * 0.05; // 5% Logic

    return (
        <div className="banca-container">
            <header className="banca-header">
                <div className="logo-wrapper">
                    <BancaLogo width={80} height={80} />
                    <h1>BANCA</h1>
                </div>
                <div className="banca-summary">
                    <div className="banca-card balance-card">
                        <h3>Saldo Atual</h3>
                        <div className={`value ${totalPnL >= 0 ? 'profit' : 'loss'}`}>
                            ${currentBalance.toFixed(2)}
                        </div>
                        <div className="sub-value">
                            Inicial: ${initialBalance.toFixed(2)} ({pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(1)}%)
                        </div>
                    </div>

                    <div className="banca-card slots-card">
                        <h3>Slots Ativos</h3>
                        <div className="slots-visual">
                            <div className={`slot ${activeSlots >= 1 ? 'occupied' : 'empty'}`}>
                                {activeSlots >= 1 ? '🔴 EM TRADE' : '🟢 LIVRE'}
                            </div>
                            <div className={`slot ${activeSlots >= 2 ? 'occupied' : 'empty'}`}>
                                {activeSlots >= 2 ? '🔴 EM TRADE' : '🟢 LIVRE'}
                            </div>
                        </div>
                        <div className="sub-value">Max 2 Sinais Simultâneos</div>
                    </div>

                    <div className="banca-card next-card">
                        <h3>Próxima Entrada</h3>
                        <div className="value">${nextEntry.toFixed(2)}</div>
                        <div className="progress-text">Ciclo Composto: {progress}/20 Trades</div>
                        <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ width: `${(progress / 20) * 100}%` }}></div>
                        </div>
                    </div>
                </div>
            </header>

            <section className="banca-history">
                <h2>Histórico de Trades (Elite)</h2>
                <div className="trades-table-container">
                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Par</th>
                                <th>Entrada</th>
                                <th>Saída</th>
                                <th>PnL ($)</th>
                                <th>ROI (%)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map(trade => (
                                <tr key={trade.id} className={trade.status.toLowerCase()}>
                                    <td>{new Date(trade.opened_at).toLocaleTimeString()}<br />
                                        <small>{new Date(trade.opened_at).toLocaleDateString()}</small>
                                    </td>
                                    <td>{trade.symbol}</td>
                                    <td>${trade.entry_price?.toFixed(4)} <small>(${trade.entry_size_usd?.toFixed(2)})</small></td>
                                    <td>{trade.exit_price ? `$${trade.exit_price.toFixed(4)}` : '-'}</td>
                                    <td className={trade.pnl_usd >= 0 ? 'profit' : 'loss'}>
                                        {trade.pnl_usd ? `$${trade.pnl_usd.toFixed(2)}` : '-'}
                                    </td>
                                    <td className={trade.pnl_percent >= 0 ? 'profit' : 'loss'}>
                                        {trade.pnl_percent ? `${(trade.pnl_percent * 100).toFixed(2)}%` : '-'}
                                    </td>
                                    <td>
                                        <span className={`status-badge ${trade.status}`}>
                                            {trade.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {trades.length === 0 && (
                                <tr>
                                    <td colSpan="7" className="no-trades">
                                        Nenhum trade de elite registrado ainda. Aguardando sinais > 75%...
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
};

export default BancaPage;
