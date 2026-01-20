import React, { useState, useMemo, useEffect } from 'react'; // HMR Reload 2
import SignalCard from './SignalCard';
import { IconHistory } from './Icons';
import './HistoryView.css';

const ITEMS_PER_PAGE = 10;

export default function HistoryView({ history, loading }) {
    const [activeFilter, setActiveFilter] = useState('ALL');
    const [currentPage, setCurrentPage] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');

    // Sort history: newest first, then by score
    const sortedHistory = useMemo(() => {
        return [...history].sort((a, b) => {
            // Sort by timestamp (newest first)
            const timeA = a.exit_timestamp || a.timestamp || 0;
            const timeB = b.exit_timestamp || b.timestamp || 0;
            if (timeB !== timeA) return timeB - timeA;

            // If timestamps are equal, sort by score (highest first)
            return (b.score || 0) - (a.score || 0);
        });
    }, [history]);

    // Calculate stats - EXPIRED separated from LOSSES
    // Calculate stats based on FILTERED history
    const stats = useMemo(() => {
        const gains = filteredHistory.filter(s => s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX');
        const losses = filteredHistory.filter(s => s.status === 'SL_HIT');
        const expired = filteredHistory.filter(s => s.status === 'EXPIRED');

        // For win rate, only count decisive signals (exclude expired)
        const decisiveTotal = gains.length + losses.length;
        const winRate = decisiveTotal > 0 ? ((gains.length / decisiveTotal) * 100).toFixed(1) : 0;

        // Calculate total ROI
        const totalROI = filteredHistory.reduce((acc, s) => acc + (s.final_roi || 0), 0);
        const avgROI = filteredHistory.length > 0 ? (totalROI / filteredHistory.length).toFixed(2) : 0;

        // Calculate avg gain and avg loss
        const avgGain = gains.length > 0
            ? (gains.reduce((acc, s) => acc + (s.final_roi || 0), 0) / gains.length).toFixed(2)
            : 0;
        const avgLoss = losses.length > 0
            ? (losses.reduce((acc, s) => acc + (s.final_roi || 0), 0) / losses.length).toFixed(2)
            : 0;

        return {
            total: filteredHistory.length,
            gains: gains.length,
            losses: losses.length,
            expired: expired.length,
            winRate,
            totalROI: totalROI.toFixed(2),
            avgROI,
            avgGain,
            avgLoss
        };
    }, [filteredHistory]);

    // Filter history based on active filter AND search term
    const filteredHistory = useMemo(() => {
        return sortedHistory.filter(s => {
            // Status Filter
            const matchesFilter = activeFilter === 'ALL' ||
                (activeFilter === 'GAINS' && (s.status === 'TP_HIT' || s.status === 'VOL_CLIMAX')) ||
                (activeFilter === 'LOSSES' && s.status === 'SL_HIT') ||
                (activeFilter === 'EXPIRED' && s.status === 'EXPIRED');

            // Search Filter
            const matchesSearch = !searchTerm ||
                s.symbol.toUpperCase().includes(searchTerm.toUpperCase());

            return matchesFilter && matchesSearch;
        });
    }, [sortedHistory, activeFilter, searchTerm]);

    // Reset page when filter or search changes
    useEffect(() => {
        setCurrentPage(1);
    }, [activeFilter, searchTerm]);

    // Pagination calculations
    const totalPages = Math.ceil(filteredHistory.length / ITEMS_PER_PAGE);

    const paginatedHistory = useMemo(() => {
        const start = (currentPage - 1) * ITEMS_PER_PAGE;
        return filteredHistory.slice(start, start + ITEMS_PER_PAGE);
    }, [filteredHistory, currentPage]);

    // Reset page if out of bounds
    useEffect(() => {
        if (currentPage > totalPages && totalPages > 0) {
            setCurrentPage(1);
        }
    }, [filteredHistory.length, totalPages, currentPage]);

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
            {/* Header with quantitative resume */}
            <div className="history-header">
                <div className="history-header-new">
                    <div className="history-title-section">
                        <div className="history-icon-wrapper">
                            <IconHistory size={28} />
                        </div>
                        <div className="history-title-text">
                            <h2>Histórico de Sinais</h2>
                            <p>Registro completo dos últimos 10 dias</p>
                        </div>
                    </div>

                    <div className="history-stats-resume">
                        <div className="resume-item">
                            <span className="resume-label">Total</span>
                            <span className="resume-value">{stats.total}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item win">
                            <span className="resume-label">Wins</span>
                            <span className="resume-value">{stats.gains}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item loss">
                            <span className="resume-label">Losses</span>
                            <span className="resume-value">{stats.losses}</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className="resume-item highlight">
                            <span className="resume-label">Win Rate</span>
                            <span className="resume-value">{stats.winRate}%</span>
                        </div>
                        <div className="resume-divider"></div>
                        <div className={`resume-item ${parseFloat(stats.totalROI) >= 0 ? 'win' : 'loss'}`}>
                            <span className="resume-label">ROI Total</span>
                            <span className="resume-value">{parseFloat(stats.totalROI) >= 0 ? '+' : ''}{stats.totalROI}%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Controls: Search and Filters */}
            <div className="history-controls-container">
                <div className="search-wrapper">
                    <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <input
                        type="text"
                        placeholder="Buscar par (ex: BTC)..."
                        className="history-search-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value.toUpperCase())}
                    />
                    {searchTerm && (
                        <button className="clear-search" onClick={() => setSearchTerm('')}>&times;</button>
                    )}
                </div>

                <div className="history-filter-tabs">
                    <button
                        className={`h-tab ${activeFilter === 'ALL' ? 'active' : ''}`}
                        onClick={() => setActiveFilter('ALL')}
                    >
                        Todos
                    </button>
                    <button
                        className={`h-tab gain ${activeFilter === 'GAINS' ? 'active' : ''}`}
                        onClick={() => setActiveFilter('GAINS')}
                    >
                        Gains
                    </button>
                    <button
                        className={`h-tab loss ${activeFilter === 'LOSSES' ? 'active' : ''}`}
                        onClick={() => setActiveFilter('LOSSES')}
                    >
                        Losses
                    </button>
                    <button
                        className={`h-tab expired ${activeFilter === 'EXPIRED' ? 'active' : ''}`}
                        onClick={() => setActiveFilter('EXPIRED')}
                    >
                        Expirados
                    </button>
                </div>
            </div>



            {paginatedHistory.length === 0 ? (
                <div className="history-empty">
                    <div className="empty-icon-circle">
                        <IconHistory size={32} />
                    </div>
                    <h3 className="empty-title">
                        {searchTerm ? `Nenhum resultado para "${searchTerm}"` : 'Nenhum sinal no histórico'}
                    </h3>
                    <p className="empty-text">
                        {searchTerm ? 'Tente buscar por outro símbolo.' : 'Sinais finalizados aparecerão aqui automaticamente.'}
                    </p>
                </div>
            ) : (
                <>
                    <div className="signals-grid">
                        {paginatedHistory.map((signal) => (
                            <SignalCard key={signal.id} signal={signal} />
                        ))}
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="pagination-controls">
                            <button
                                className="pagination-btn"
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                            >
                                ← Anterior
                            </button>
                            <span className="pagination-info">
                                Página {currentPage} de {totalPages} ({filteredHistory.length} sinais encontrados)
                            </span>
                            <button
                                className="pagination-btn"
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                            >
                                Próximo →
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
