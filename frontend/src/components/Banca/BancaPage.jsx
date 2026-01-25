import React, { useState, useEffect } from 'react';
import ErrorBoundary from '../Common/ErrorBoundary';
import SignalChart from './SignalChart';

// Premium Stat Card with gradient background and glow effects
const StatCard = ({ label, value, subValue, type = 'neutral', icon }) => {
    const getGradient = () => {
        if (type === 'profit') return 'from-emerald-500/20 via-teal-500/10 to-transparent';
        if (type === 'loss') return 'from-red-500/20 via-rose-500/10 to-transparent';
        return 'from-blue-500/20 via-indigo-500/10 to-transparent';
    };

    const getBorderColor = () => {
        if (type === 'profit') return 'border-emerald-500/30 hover:border-emerald-400/50';
        if (type === 'loss') return 'border-red-500/30 hover:border-red-400/50';
        return 'border-blue-500/30 hover:border-blue-400/50';
    };

    const getTextColor = () => {
        if (type === 'profit') return 'text-emerald-400';
        if (type === 'loss') return 'text-red-400';
        return 'text-blue-400';
    };

    const getGlow = () => {
        if (type === 'profit') return 'shadow-emerald-500/10';
        if (type === 'loss') return 'shadow-red-500/10';
        return 'shadow-blue-500/10';
    };

    return (
        <div className={`
            relative overflow-hidden
            bg-gradient-to-br ${getGradient()}
            backdrop-blur-xl
            border ${getBorderColor()}
            rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6
            shadow-xl ${getGlow()}
            transition-all duration-300
            hover:scale-[1.02] hover:shadow-2xl
            group
        `}>
            {/* Decorative glow orb */}
            <div className={`absolute -top-8 -right-8 w-16 sm:w-24 h-16 sm:h-24 rounded-full blur-3xl ${type === 'profit' ? 'bg-emerald-500/20' : type === 'loss' ? 'bg-red-500/20' : 'bg-blue-500/20'} group-hover:opacity-75 transition-opacity`} />

            <div className="relative z-10">
                <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                    {icon && <span className={`material-symbols-outlined text-xs sm:text-sm ${getTextColor()}`}>{icon}</span>}
                    <span className="text-[8px] sm:text-[10px] font-bold tracking-[0.15em] sm:tracking-[0.2em] text-gray-400 uppercase truncate">{label}</span>
                </div>
                <div className="space-y-0.5 sm:space-y-1">
                    <span className="text-lg sm:text-2xl md:text-3xl font-black text-white block tracking-tight">{value}</span>
                    {subValue && (
                        <span className={`text-[10px] sm:text-xs font-semibold ${getTextColor()} flex items-center gap-1 truncate`}>
                            {type === 'profit' && <span className="material-symbols-outlined text-[10px] sm:text-xs">trending_up</span>}
                            {type === 'loss' && <span className="material-symbols-outlined text-[10px] sm:text-xs">trending_down</span>}
                            <span className="truncate">{subValue}</span>
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};

// Trading Status Card Component - Mobile Optimized
const TradingStatusCard = ({ status }) => (
    <div className="relative overflow-hidden bg-gradient-to-br from-violet-600/20 via-purple-500/10 to-fuchsia-500/5 backdrop-blur-xl border border-violet-500/30 rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 shadow-xl group hover:border-violet-400/50 transition-all duration-300">
        {/* Animated background grid */}
        <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.1)_1px,transparent_1px)] bg-[size:20px_20px]" />
        </div>

        {/* Pulsing orb */}
        <div className="absolute top-2 sm:top-4 right-2 sm:right-4">
            <div className="relative">
                <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-violet-400 animate-ping absolute" />
                <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-violet-400 relative" />
            </div>
        </div>

        <div className="relative z-10">
            <span className="text-[8px] sm:text-[10px] uppercase tracking-[0.15em] sm:tracking-[0.2em] text-violet-400 font-bold mb-2 sm:mb-3 block">CAPITÃO DA BANCA</span>
            <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
                    <span className="material-symbols-outlined text-white text-sm sm:text-lg">psychology</span>
                </div>
                <div>
                    <div className="text-white font-bold text-xs sm:text-sm">ELITE MANAGER AGENT</div>
                    <div className="text-violet-300 text-[10px] sm:text-xs">
                        {status?.elite_agent?.current_strategy || 'Analisando Mercado'}
                    </div>
                </div>
            </div>

            {/* Slots usage */}
            <div className="space-y-1.5 sm:space-y-2">
                <div className="flex justify-between text-[8px] sm:text-[10px] text-gray-400">
                    <span>Performance Sniper (Slots)</span>
                    <span className="text-violet-400">{status?.active_slots_used || 0} / 10 ATIVOS</span>
                </div>
                <div className="h-1 sm:h-1.5 bg-gray-800/50 rounded-full overflow-hidden flex gap-0.5">
                    {[...Array(10)].map((_, i) => (
                        <div
                            key={i}
                            className={`h-full flex-1 rounded-full ${(status?.active_slots_used || 0) > i
                                ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]'
                                : 'bg-gray-700/50'
                                }`}
                        />
                    ))}
                </div>
            </div>
        </div>
    </div>
);

const BancaPage = () => {
    const [status, setStatus] = useState(null);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTrade, setSelectedTrade] = useState(null);
    const [viewMode, setViewMode] = useState('active'); // 'active' | 'history'

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    // Auto-select the first trade when trades are loaded
    useEffect(() => {
        if (trades.length > 0 && !selectedTrade) {
            setSelectedTrade(trades[0]);
        }
    }, [trades]);

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
                const sorted = Array.isArray(tData) ? [...tData].sort((a, b) => new Date(b.opened_at) - new Date(a.opened_at)) : [];
                setTrades(sorted);

                // SYNC SELECTED TRADE: Update with latest telemetry and price
                if (selectedTrade) {
                    const updated = sorted.find(t => t.id === selectedTrade.id);
                    if (updated) setSelectedTrade(updated);
                }
            }
        } catch (error) {
            console.error("Error fetching bankroll data:", error);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (val) => {
        const num = Number(val);
        return isNaN(num) ? '$0.00' : `$${num.toFixed(2)}`;
    };

    const activeTrades = trades.filter(t => t.status === 'OPEN');
    const historyTrades = trades.filter(t => t.status !== 'OPEN');
    const displayedTrades = viewMode === 'active' ? activeTrades : historyTrades;

    if (loading && !status) {
        return (
            <div className="min-h-screen bg-[#06080a] flex items-center justify-center">
                <div className="text-center">
                    <div className="relative w-16 h-16 mx-auto mb-6">
                        <div className="absolute inset-0 rounded-full border-2 border-emerald-500/30 animate-ping" />
                        <div className="absolute inset-2 rounded-full border-2 border-emerald-400/50 animate-pulse" />
                        <div className="absolute inset-4 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 animate-pulse" />
                    </div>
                    <div className="text-emerald-400 font-bold tracking-[0.3em] text-sm animate-pulse">
                        INICIANDO SISTEMA NEURAL
                    </div>
                    <div className="text-gray-600 text-xs mt-2 tracking-wider">
                        Carregando dados da banca...
                    </div>
                </div>
            </div>
        );
    }

    return (
        <ErrorBoundary>
            <div className="min-h-screen bg-[#06080a] text-gray-200 font-display">
                {/* Background decorative elements */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-[128px]" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-[128px]" />
                </div>

                <div className="relative z-10 p-2 sm:p-4 md:p-8 max-w-[1800px] mx-auto">

                    {/* PREMIUM HEADER */}
                    <header className="mb-4 sm:mb-6 md:mb-10">
                        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3 sm:gap-6">
                            {/* Logo & Title */}
                            <div className="flex items-center gap-2 sm:gap-4">
                                <img
                                    src="/Robo.png"
                                    alt="Robot Logo"
                                    className="w-12 h-12 sm:w-16 sm:h-16 md:w-20 md:h-20 object-contain drop-shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                                />
                                <div>
                                    <img
                                        src="/logobanca.png"
                                        alt="10D Banca"
                                        className="h-8 sm:h-10 md:h-12 object-contain"
                                    />
                                    <div className="flex items-center gap-1.5 sm:gap-2 mt-1">
                                        <span className="relative flex h-2 w-2 sm:h-2.5 sm:w-2.5">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 sm:h-2.5 sm:w-2.5 bg-emerald-500"></span>
                                        </span>
                                        <span className="text-[10px] sm:text-xs font-semibold text-emerald-400 tracking-wider uppercase">Neural Online</span>
                                    </div>
                                </div>
                            </div>

                            {/* Controls */}
                            {status && (
                                <div className="flex flex-wrap items-center gap-2 sm:gap-4">
                                    {/* Cycle Counter */}
                                    <div className="flex items-center gap-2 sm:gap-3 px-3 py-2 sm:px-5 sm:py-3 bg-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl border border-gray-800/50">
                                        <div className="text-right">
                                            <span className="text-[8px] sm:text-[10px] text-gray-500 uppercase tracking-wider block">Ciclo</span>
                                            <div className="flex items-baseline gap-0.5 sm:gap-1">
                                                <span className="text-lg sm:text-2xl font-black text-white">{status.trade_count_cycle}</span>
                                                <span className="text-gray-600 font-light text-sm sm:text-base">/20</span>
                                            </div>
                                        </div>
                                        <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border border-gray-700/50">
                                            <svg className="w-4 h-4 sm:w-6 sm:h-6 text-gray-400" viewBox="0 0 36 36">
                                                <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.2" />
                                                <circle cx="18" cy="18" r="16" fill="none" stroke="url(#cycleGradient)" strokeWidth="2"
                                                    strokeDasharray={`${(status.trade_count_cycle / 20) * 100}, 100`}
                                                    strokeLinecap="round" transform="rotate(-90 18 18)" />
                                                <defs>
                                                    <linearGradient id="cycleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                        <stop offset="0%" stopColor="#10b981" />
                                                        <stop offset="100%" stopColor="#06b6d4" />
                                                    </linearGradient>
                                                </defs>
                                            </svg>
                                        </div>
                                    </div>

                                    {/* Push Notification Button */}
                                    <button
                                        onClick={async () => {
                                            try {
                                                // 1. Request Permission
                                                const permission = await Notification.requestPermission();
                                                if (permission !== 'granted') {
                                                    alert('Permissão de notificação negada. Ative nas configurações do navegador.');
                                                    return;
                                                }

                                                // 2. Register Service Worker
                                                const register = await navigator.serviceWorker.register('/service-worker.js', {
                                                    scope: '/'
                                                });

                                                // 3. Get VAPID Public Key
                                                const keyRes = await fetch('/api/push/vapid-public-key');
                                                const { publicKey } = await keyRes.json();

                                                // 4. Subscribe
                                                const subscription = await register.pushManager.subscribe({
                                                    userVisibleOnly: true,
                                                    applicationServerKey: (() => {
                                                        const padding = '='.repeat((4 - (publicKey.length % 4)) % 4);
                                                        const base64 = (publicKey + padding).replace(/-/g, '+').replace(/_/g, '/');
                                                        const rawData = window.atob(base64);
                                                        const outputArray = new Uint8Array(rawData.length);
                                                        for (let i = 0; i < rawData.length; ++i) {
                                                            outputArray[i] = rawData.charCodeAt(i);
                                                        }
                                                        return outputArray;
                                                    })()
                                                });

                                                // 5. Send to Server
                                                const saveRes = await fetch('/api/push/subscribe', {
                                                    method: 'POST',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({ subscription, userId: 'default_user' })
                                                });

                                                if (saveRes.ok) {
                                                    alert('🦅 Capitão Conectado! Você receberá alertas no celular.');
                                                }
                                            } catch (err) {
                                                console.error('Push error:', err);
                                                alert('Erro ao ativar notificações: ' + err.message);
                                            }
                                        }}
                                        className="group flex items-center gap-1.5 sm:gap-2 px-3 py-2 sm:px-5 sm:py-3 bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/30 hover:border-emerald-500/50 rounded-xl sm:rounded-2xl text-emerald-400 hover:text-emerald-300 transition-all duration-300"
                                    >
                                        <span className="material-symbols-outlined text-sm sm:text-lg animate-bounce">notifications_active</span>
                                        <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider hidden sm:block">Ativar Alertas</span>
                                    </button>

                                    {/* Reset Button */}
                                    <button
                                        onClick={async () => {
                                            if (window.confirm('TEM CERTEZA? Isso resetará toda a banca para $1000 e apagará o histórico.')) {
                                                try {
                                                    const res = await fetch('/api/bankroll/reset', { method: 'POST' });
                                                    if (res.ok) {
                                                        alert('Banca resetada com sucesso!');
                                                        fetchData();
                                                    }
                                                } catch (e) {
                                                    alert('Erro ao resetar: ' + e);
                                                }
                                            }
                                        }}
                                        className="group flex items-center gap-1.5 sm:gap-2 px-3 py-2 sm:px-5 sm:py-3 bg-red-950/30 hover:bg-red-900/40 border border-red-500/30 hover:border-red-500/50 rounded-xl sm:rounded-2xl text-red-400 hover:text-red-300 transition-all duration-300"
                                    >
                                        <span className="material-symbols-outlined text-sm sm:text-lg group-hover:rotate-180 transition-transform duration-500">restart_alt</span>
                                        <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider hidden sm:block">Resetar</span>
                                    </button>
                                </div>
                            )}
                        </div>
                        {/* RISK MANAGEMENT HEADER */}
                        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-red-950/20 border border-red-500/20 rounded-xl p-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-red-500/10 rounded-lg">
                                        <span className="material-symbols-outlined text-red-400">shield</span>
                                    </div>
                                    <div>
                                        <h4 className="text-red-200 font-bold text-sm">RISK MANAGEMENT</h4>
                                        <p className="text-red-400/60 text-xs">Proteção Ativa</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="block text-xl font-bold text-red-400">20% MAX</span>
                                    <span className="text-xs text-red-500/60">EXPOSURE CAP</span>
                                </div>
                            </div>

                            <div className="bg-violet-950/20 border border-violet-500/20 rounded-xl p-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-violet-500/10 rounded-lg">
                                        <span className="material-symbols-outlined text-violet-400">dataset</span>
                                    </div>
                                    <div>
                                        <h4 className="text-violet-200 font-bold text-sm">ELITE SLOTS</h4>
                                        <p className="text-violet-400/60 text-xs">Vagas para Sinais</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="block text-xl font-bold text-violet-400">{status?.active_slots_used || 0} / 10</span>
                                    <span className="text-xs text-violet-500/60">ACTIVE TRADES</span>
                                </div>
                            </div>
                        </div>

                    </header>

                    {/* MAIN GRID */}
                    <div className="grid grid-cols-1 xl:grid-cols-4 gap-3 sm:gap-6 mb-4 sm:mb-8">

                        {/* LEFT COL: CHART (3 spans) */}
                        <div className="xl:col-span-3">
                            <div className="bg-gray-900/40 backdrop-blur-xl rounded-xl sm:rounded-3xl border border-gray-800/50 overflow-hidden shadow-2xl h-[280px] sm:h-[400px] md:h-[520px]">
                                {/* Chart Header */}
                                <div className="px-3 py-2.5 sm:px-5 sm:py-4 border-b border-gray-800/50 bg-gray-900/60 flex justify-between items-center">
                                    <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                                        <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-md sm:rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center border border-emerald-500/30 shrink-0">
                                            <span className="material-symbols-outlined text-emerald-400 text-xs sm:text-sm">monitoring</span>
                                        </div>
                                        <div className="min-w-0">
                                            <h3 className="font-bold text-white text-xs sm:text-sm md:text-base truncate">
                                                {selectedTrade ? `${selectedTrade.symbol}` : 'MONITORAMENTO'}
                                            </h3>
                                            {selectedTrade && (
                                                <div className="flex items-center gap-1.5 sm:gap-2 mt-0.5">
                                                    <span className={`text-[10px] sm:text-xs font-bold px-1.5 sm:px-2 py-0.5 rounded ${selectedTrade.direction === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {selectedTrade.direction}
                                                    </span>
                                                    <span className="text-gray-500 text-[10px] sm:text-xs hidden sm:inline">•</span>
                                                    <span className="text-gray-400 text-[10px] sm:text-xs font-mono hidden sm:inline">Entry: {formatCurrency(selectedTrade.entry_price)}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {selectedTrade && (
                                        <div className="hidden md:flex items-center gap-4 text-xs">
                                            <div className="text-center px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                                <span className="text-gray-500 block">TP</span>
                                                <span className="text-emerald-400 font-bold font-mono">{formatCurrency(selectedTrade.take_profit)}</span>
                                            </div>
                                            <div className="text-center px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
                                                <span className="text-gray-500 block">SL</span>
                                                <span className="text-red-400 font-bold font-mono">{formatCurrency(selectedTrade.stop_loss)}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Chart Content */}
                                <div className="h-[calc(100%-73px)] relative bg-gradient-to-b from-gray-900/20 to-gray-950/40">
                                    {selectedTrade ? (
                                        <SignalChart
                                            symbol={selectedTrade.symbol}
                                            entryPrice={selectedTrade.entry_price}
                                            stopLoss={selectedTrade.stop_loss}
                                            takeProfit={selectedTrade.take_profit}
                                            direction={selectedTrade.direction}
                                            openedAt={selectedTrade.opened_at}
                                            currentPrice={selectedTrade.current_price}
                                            telemetry={selectedTrade.telemetry}
                                        />
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center p-8">
                                            <div className="w-20 h-20 rounded-2xl bg-gray-800/50 flex items-center justify-center mb-4 border border-gray-700/50">
                                                <span className="material-symbols-outlined text-gray-600 text-3xl">candlestick_chart</span>
                                            </div>
                                            <p className="text-gray-500 text-center max-w-xs">
                                                Selecione uma operação abaixo para visualizar o gráfico em tempo real
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* RIGHT COL: STATS (1 span) */}
                        <div className="grid grid-cols-2 xl:grid-cols-1 gap-2 sm:gap-4 xl:gap-5 content-start">
                            {status && (
                                <>
                                    <StatCard
                                        label="Saldo Atual"
                                        value={formatCurrency(status.current_balance)}
                                        subValue={`${status.total_pnl >= 0 ? '+' : ''}${formatCurrency(status.total_pnl)}`}
                                        type={status.total_pnl >= 0 ? 'profit' : 'loss'}
                                        icon="account_balance_wallet"
                                    />
                                    <StatCard
                                        label="ROI do Ciclo"
                                        value={`${Number(status.roi_percentage || 0).toFixed(2)}%`}
                                        subValue="Retorno sobre investimento"
                                        type={status.roi_percentage >= 0 ? 'profit' : 'loss'}
                                        icon="trending_up"
                                    />
                                    <div className="col-span-2 xl:col-span-1">
                                        <TradingStatusCard status={status} />
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* BOTTOM: HISTORY TABLE */}
                    <div className="bg-gray-900/40 backdrop-blur-xl rounded-xl sm:rounded-3xl border border-gray-800/50 overflow-hidden shadow-2xl">
                        {/* Table Header with Tabs */}
                        <div className="px-3 py-3 sm:px-6 sm:py-5 border-b border-gray-800/50 bg-gray-900/60 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-4">
                            <div className="flex items-center gap-4">
                                {/* TAB: ACTIVE */}
                                <button
                                    onClick={() => setViewMode('active')}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${viewMode === 'active'
                                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-500/10'
                                        : 'hover:bg-gray-800/50 text-gray-400'
                                        }`}
                                >
                                    <div className={`w-2 h-2 rounded-full ${viewMode === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}`} />
                                    <span className="font-bold text-sm">Abertas</span>
                                    <span className="text-xs opacity-60 bg-black/20 px-1.5 rounded">{activeTrades.length}</span>
                                </button>

                                {/* TAB: HISTORY */}
                                <button
                                    onClick={() => setViewMode('history')}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${viewMode === 'history'
                                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                        : 'hover:bg-gray-800/50 text-gray-400'
                                        }`}
                                >
                                    <span className="material-symbols-outlined text-sm">history</span>
                                    <span className="font-bold text-sm">Concluídas</span>
                                    <span className="text-xs opacity-60 bg-black/20 px-1.5 rounded">{historyTrades.length}</span>
                                </button>
                            </div>
                        </div>

                        {/* Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-gray-800/50 text-[8px] sm:text-[10px] uppercase tracking-wider text-gray-500 font-semibold bg-gray-950/30">
                                        <th className="p-2 sm:p-4 md:p-5">Data</th>
                                        <th className="p-2 sm:p-4 md:p-5">Par</th>
                                        <th className="p-2 sm:p-4 md:p-5">Dir</th>
                                        <th className="p-2 sm:p-4 md:p-5 text-center">Status</th>
                                        <th className="p-2 sm:p-4 md:p-5 text-right hidden sm:table-cell">Entrada</th>
                                        <th className="p-2 sm:p-4 md:p-5 text-right hidden sm:table-cell">Saída</th>
                                        <th className="p-2 sm:p-4 md:p-5 text-right">P/L</th>
                                    </tr>
                                </thead>
                                <tbody className="text-xs sm:text-sm">
                                    {displayedTrades.length > 0 ? displayedTrades.map((trade, index) => (
                                        <tr
                                            key={trade.id}
                                            onClick={() => {
                                                setSelectedTrade(trade);
                                                if (window.innerWidth < 1280) {
                                                    window.scrollTo({ top: 0, behavior: 'smooth' });
                                                }
                                            }}
                                            className={`
                                                border-b border-gray-800/30 
                                                cursor-pointer transition-all duration-200
                                                ${selectedTrade && selectedTrade.id === trade.id
                                                    ? 'bg-emerald-500/10 border-l-4 border-l-emerald-500'
                                                    : 'hover:bg-gray-800/30'}
                                            `}
                                            style={{ animationDelay: `${index * 50}ms` }}
                                        >
                                            <td className="p-2 sm:p-4 md:p-5">
                                                <div className="text-white font-medium text-[10px] sm:text-sm">{new Date(trade.opened_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}</div>
                                                <div className="text-gray-500 text-[8px] sm:text-xs mt-0.5">{new Date(trade.opened_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</div>
                                            </td>
                                            <td className="p-2 sm:p-4 md:p-5">
                                                <span className="font-bold text-white bg-gray-800/50 px-1.5 py-1 sm:px-3 sm:py-1.5 rounded-md sm:rounded-lg text-[10px] sm:text-sm">{trade.symbol.replace('USDT', '')}</span>
                                            </td>
                                            <td className="p-2 sm:p-4 md:p-5">
                                                <span className={`
                                                    inline-flex items-center gap-1 sm:gap-1.5 px-1.5 py-1 sm:px-3 sm:py-1.5 rounded-md sm:rounded-lg text-[10px] sm:text-xs font-bold
                                                    ${trade.direction === 'LONG'
                                                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                                        : 'bg-red-500/15 text-red-400 border border-red-500/30'}
                                                `}>
                                                    <span className="material-symbols-outlined text-[10px] sm:text-xs">
                                                        {trade.direction === 'LONG' ? 'arrow_upward' : 'arrow_downward'}
                                                    </span>
                                                    <span className="hidden sm:inline">{trade.direction}</span>
                                                </span>
                                            </td>
                                            <td className="p-2 sm:p-4 md:p-5 text-center">
                                                <span className={`
                                                    px-1.5 py-1 sm:px-3 sm:py-1.5 rounded-full text-[8px] sm:text-[10px] font-bold uppercase tracking-wide
                                                    ${trade.status === 'OPEN'
                                                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse'
                                                        : trade.pnl_usd > 0
                                                            ? 'bg-emerald-500/20 text-emerald-400'
                                                            : 'bg-red-500/20 text-red-400'}
                                                `}>
                                                    {trade.status === 'OPEN' ? 'OPEN' : trade.pnl_usd > 0 ? 'WIN' : 'LOSS'}
                                                </span>
                                            </td>
                                            <td className="p-2 sm:p-4 md:p-5 text-right font-mono text-gray-300 hidden sm:table-cell text-xs sm:text-sm">{formatCurrency(trade.entry_price)}</td>
                                            <td className="p-2 sm:p-4 md:p-5 text-right font-mono text-gray-300 hidden sm:table-cell text-xs sm:text-sm">{trade.exit_price ? formatCurrency(trade.exit_price) : '—'}</td>
                                            <td className="p-2 sm:p-4 md:p-5 text-right">
                                                <div className="flex flex-col items-end">
                                                    <span className={`
                                                        font-bold font-mono text-xs sm:text-base
                                                        ${(trade.current_roi || trade.pnl_usd) >= 0 ? 'text-emerald-400' : 'text-red-400'}
                                                    `}>
                                                        {trade.status === 'OPEN' ? `${trade.current_roi > 0 ? '+' : ''}${trade.current_roi || 0}%` : formatCurrency(trade.pnl_usd)}
                                                    </span>
                                                    {trade.status === 'OPEN' && trade.telemetry && (
                                                        <span className="text-[7px] sm:text-[9px] text-blue-400/70 truncate max-w-[80px] sm:max-w-[120px] uppercase font-bold tracking-tighter">
                                                            {trade.telemetry.substring(0, 20)}...
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="7" className="p-16 text-center">
                                                <div className="flex flex-col items-center">
                                                    <div className="w-16 h-16 rounded-2xl bg-gray-800/50 flex items-center justify-center mb-4 border border-gray-700/50">
                                                        <span className="material-symbols-outlined text-gray-600 text-2xl">inbox</span>
                                                    </div>
                                                    <p className="text-gray-500">Nenhuma operação registrada neste ciclo</p>
                                                    <p className="text-gray-600 text-sm mt-1">As operações aparecerão aqui quando iniciadas</p>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* FOOTER BRANDING */}
                    <div className="mt-8 sm:mt-12 mb-4 sm:mb-8 flex justify-center opacity-40 hover:opacity-80 transition-opacity duration-500">
                        <img
                            src="/logomarca1Ccolor.png"
                            alt="10D Futures Branding"
                            className="h-12 sm:h-16 object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                        />
                    </div>

                </div>
            </div>
        </ErrorBoundary>
    );
};

export default BancaPage;
