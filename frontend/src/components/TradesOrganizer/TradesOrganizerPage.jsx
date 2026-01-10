import React, { useEffect, useMemo, useState } from 'react';

// Plan constants
const TOTAL_DAYS = 30;
const TRADES_PER_DAY = 10;
const INITIAL_STAKE_PERCENTAGE = 0.06; // 6%

// Storage key
const STORAGE_KEY = 'trading_plan_data_v1';

/**
 * Currency formatter
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
    }).format(value);
}

/**
 * Calculate order value with doubling every 2 days
 */
function calculateOrderValue(day, initialOrderValue) {
    if (day < 1 || day > TOTAL_DAYS) return 0;
    const doublingFactor = Math.floor((day - 1) / 2);
    return initialOrderValue * Math.pow(2, doublingFactor);
}

/**
 * Generate full plan
 */
function generatePlan(bancaInicial, existingResults = []) {
    const plan = [];
    const initialOrderValue = bancaInicial * INITIAL_STAKE_PERCENTAGE;
    let cumulativeTotal = 0;

    const existingMap = new Map(existingResults.map((r) => [r.day, r.trades]));

    for (let day = 1; day <= TOTAL_DAYS; day++) {
        const orderValue = calculateOrderValue(day, initialOrderValue);
        const dailyGoal = orderValue * TRADES_PER_DAY;
        const existingTrades = existingMap.get(day) || [];

        const trades = Array.from({ length: TRADES_PER_DAY }, (_, i) => {
            const trade = existingTrades[i] || { coin: '', resultValue: 0 };
            return {
                coin: trade.coin || '',
                resultValue: Number(trade.resultValue) || 0
            };
        });

        const successTrades = trades.filter((t) => t.resultValue > 0).length;
        const dailyResult = trades.reduce((sum, t) => sum + t.resultValue, 0);
        cumulativeTotal += dailyResult;

        plan.push({
            day,
            orderValue,
            dailyGoal,
            successTrades,
            trades,
            dailyResult,
            cumulativeTotal,
        });
    }

    return plan;
}

const TradesOrganizerPage = () => {
    const [planData, setPlanData] = useState({
        bancaInicial: 1000,
        dailyResults: [],
    });
    const [message, setMessage] = useState('');
    const [modalDay, setModalDay] = useState(null);

    useEffect(() => {
        async function loadData() {
            try {
                // Try backend first
                const res = await fetch('/api/users/artifacts/trading-plan');
                if (res.ok) {
                    const json = await res.json();
                    if (json?.success && json?.data) {
                        setPlanData(json.data);
                        return;
                    }
                }

                // Fallback to localStorage
                const local = localStorage.getItem(STORAGE_KEY);
                if (local) {
                    setPlanData(JSON.parse(local));
                }
            } catch (e) {
                console.warn('Error loading plan data:', e);
            }
        }
        loadData();
    }, []);

    const fullPlan = useMemo(
        () => generatePlan(planData.bancaInicial, planData.dailyResults),
        [planData]
    );

    const saveToAll = async (next) => {
        setPlanData(next);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        try {
            await fetch('/api/users/artifacts/trading-plan', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(next)
            });
        } catch (e) {
            console.error('Error saving to backend:', e);
        }
    };

    const handleBankChange = (e) => {
        const value = Math.max(10, parseFloat(e.target.value) || 0);
        saveToAll({ ...planData, bancaInicial: value });
    };

    const handleResetPlan = async () => {
        if (!window.confirm('Deseja resetar todos os dados do organizador?')) return;
        const reset = { bancaInicial: 1000, dailyResults: [] };
        saveToAll(reset);
        setMessage('Dados resetados.');
        setTimeout(() => setMessage(''), 2000);
    };

    const saveDailyTrades = (trades) => {
        if (modalDay == null) return;
        const nextResults = [...planData.dailyResults];
        const existsIndex = nextResults.findIndex((r) => r.day === modalDay);

        const normalized = trades.map(t => ({
            coin: t.coin.trim() || 'N/A',
            resultValue: parseFloat(t.resultValue) || 0
        }));

        if (existsIndex >= 0) {
            nextResults[existsIndex] = { day: modalDay, trades: normalized };
        } else {
            nextResults.push({ day: modalDay, trades: normalized });
        }

        saveToAll({ ...planData, dailyResults: nextResults });
        setMessage(`Dia ${modalDay} salvo!`);
        setTimeout(() => setMessage(''), 2000);
        setModalDay(null);
    };

    const lastCumulativeTotal = fullPlan.length > 0 ? fullPlan[fullPlan.length - 1].cumulativeTotal : 0;

    return (
        <div className="trades-organizer">
            <header className="page-header-simple">
                <div className="header-text">
                    <h1>Organizador de Trades</h1>
                    <p>Planejamento de 30 dias com juros compostos</p>
                </div>
                <div className="header-actions">
                    <button className="btn-secondary" onClick={handleResetPlan}>Limpar Tudo</button>
                </div>
            </header>

            <div className="organizer-config-card glass-card">
                <div className="config-item">
                    <label>Banca Inicial (USD)</label>
                    <input
                        type="number"
                        value={planData.bancaInicial}
                        onChange={handleBankChange}
                        className="dark-input"
                    />
                </div>
                <div className="stats-summary-box">
                    <span className="label">Total Acumulado</span>
                    <span className="value accent-text">{formatCurrency(lastCumulativeTotal)}</span>
                </div>
            </div>

            <div className="plan-table-container glass-card">
                <table className="plan-table">
                    <thead>
                        <tr>
                            <th>Dia</th>
                            <th>Stake ($)</th>
                            <th>Meta ($)</th>
                            <th>Ações</th>
                            <th>Resultado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fullPlan.map((dp) => (
                            <tr key={dp.day}>
                                <td><span className="day-badge">{dp.day}</span></td>
                                <td>{formatCurrency(dp.orderValue)}</td>
                                <td className="goal-text">{formatCurrency(dp.dailyGoal)}</td>
                                <td>
                                    <button
                                        className={`btn-table ${dp.successTrades > 0 ? 'active' : ''}`}
                                        onClick={() => setModalDay(dp.day)}
                                    >
                                        {dp.successTrades} Trades
                                    </button>
                                </td>
                                <td className={`result-text ${dp.dailyResult > 0 ? 'positive' : dp.dailyResult < 0 ? 'negative' : ''}`}>
                                    {formatCurrency(dp.dailyResult)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {message && <div className="floating-toast">{message}</div>}

            {modalDay !== null && (
                <TradeModal
                    day={modalDay}
                    trades={fullPlan.find(p => p.day === modalDay).trades}
                    onClose={() => setModalDay(null)}
                    onSave={saveDailyTrades}
                />
            )}
        </div>
    );
};

const TradeModal = ({ day, trades, onClose, onSave }) => {
    const [localTrades, setLocalTrades] = useState(trades);

    const updateTrade = (idx, field, val) => {
        const next = [...localTrades];
        next[idx] = { ...next[idx], [field]: val };
        setLocalTrades(next);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content glass-card" onClick={e => e.stopPropagation()}>
                <h3>Investimentos - Dia {day}</h3>
                <div className="trades-list">
                    {localTrades.map((t, i) => (
                        <div key={i} className="trade-row">
                            <span className="idx">#{i + 1}</span>
                            <input
                                placeholder="Moeda"
                                value={t.coin}
                                onChange={e => updateTrade(i, 'coin', e.target.value)}
                            />
                            <input
                                type="number"
                                placeholder="Resultado"
                                value={t.resultValue}
                                onChange={e => updateTrade(i, 'resultValue', e.target.value)}
                            />
                        </div>
                    ))}
                </div>
                <div className="modal-footer">
                    <button className="btn-secondary" onClick={onClose}>Cancelar</button>
                    <button className="btn-primary" onClick={() => onSave(localTrades)}>Salvar Dia</button>
                </div>
            </div>
        </div>
    );
};

export default TradesOrganizerPage;
