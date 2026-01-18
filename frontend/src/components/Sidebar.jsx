import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { IconDashboard, IconOrganizer, IconHistory, IconSettings, IconSun, IconMoon, IconLogout, IconAI, IconBrain } from './Icons';

export default function Sidebar({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const { t } = useTranslation();
    const [showAIMenu, setShowAIMenu] = useState(false);
    const [show10MMenu, setShow10MMenu] = useState(false);
    const aiMenuRef = useRef(null);
    const tenMMenuRef = useRef(null);

    const menuItems = [
        { id: 'dashboard', icon: <IconDashboard />, label: t('nav.invest'), mobileLabel: t('nav.invest') },
        { id: 'signal-journey', icon: <IconBrain />, label: t('nav.signalJourney'), mobileLabel: 'Journey' },
        { id: 'organizer', icon: <IconOrganizer />, label: t('nav.organizer'), mobileLabel: '10M' },
    ];

    // Legacy AI menu items - kept for backwards compatibility but not shown
    const aiMenuItems = [];

    const tenMMenuItems = [
        { id: 'signal-journey', icon: <IconBrain />, label: t('nav.signalJourney') },
        { id: 'organizer', icon: <IconOrganizer />, label: t('nav.organizer') },
    ];

    // Close menus when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (aiMenuRef.current && !aiMenuRef.current.contains(event.target)) {
                setShowAIMenu(false);
            }
            if (tenMMenuRef.current && !tenMMenuRef.current.contains(event.target)) {
                setShow10MMenu(false);
            }
        };

        if (showAIMenu || show10MMenu) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showAIMenu, show10MMenu]);

    const handleAIClick = () => {
        setShowAIMenu(!showAIMenu);
        setShow10MMenu(false);
    };

    const handle10MClick = () => {
        setShow10MMenu(!show10MMenu);
        setShowAIMenu(false);
    };

    const handleAIItemClick = (id) => {
        onNavigate(id);
        setShowAIMenu(false);
    };

    const handle10MItemClick = (id) => {
        onNavigate(id);
        setShow10MMenu(false);
    };

    return (
        <>
            {/* Desktop Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <img src="/logo10D.png" alt="10D Logo" className="sidebar-logo" />
                </div>

                <nav className="sidebar-nav">
                    {menuItems.map(item => (
                        <button
                            key={item.id}
                            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
                            onClick={() => onNavigate(item.id)}
                            title={item.label}
                        >
                            <div className="nav-icon-wrapper">
                                {item.icon}
                            </div>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}

                    {aiMenuItems.map(item => (
                        <button
                            key={item.id}
                            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
                            onClick={() => onNavigate(item.id)}
                            title={item.label}
                        >
                            <div className="nav-icon-wrapper">
                                {item.icon}
                            </div>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}

                    <button
                        className={`nav-item ${currentPage === 'settings' ? 'active' : ''}`}
                        onClick={() => onNavigate('settings')}
                        title="Configurações"
                    >
                        <div className="nav-icon-wrapper">
                            <IconSettings />
                        </div>
                        <span className="nav-label">Configurações</span>
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <button
                        className="theme-toggle"
                        onClick={onToggleTheme}
                        title={theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}
                    >
                        <div className="nav-icon-wrapper">
                            {theme === 'dark' ? <IconSun /> : <IconMoon />}
                        </div>
                    </button>
                    <button
                        className="theme-toggle logout-btn"
                        onClick={onLogout}
                        title="Sair"
                    >
                        <div className="nav-icon-wrapper">
                            <IconLogout />
                        </div>
                    </button>
                </div>
            </aside>

            {/* Backdrop for submenus */}
            {(showAIMenu || show10MMenu) && (
                <div
                    className="mobile-submenu-backdrop"
                    onClick={() => {
                        setShowAIMenu(false);
                        setShow10MMenu(false);
                    }}
                />
            )}

            {/* Mobile Bottom Navigation */}
            <nav className="mobile-nav">
                {/* Invest */}
                <button
                    className={`mobile-nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
                    onClick={() => onNavigate('dashboard')}
                    title="Invest"
                >
                    <div className="nav-icon-wrapper">
                        <IconDashboard />
                    </div>
                </button>

                {/* 10M - Com Submenu */}
                <button
                    className={`mobile-nav-item ${(currentPage === 'live-monitor' || currentPage === 'organizer' || currentPage === 'history' || show10MMenu) ? 'active' : ''}`}
                    onClick={handle10MClick}
                    title="10M"
                >
                    <div className="nav-icon-wrapper">
                        <IconOrganizer />
                    </div>
                </button>

                {/* AI - Central Destacado - Navega direto para Signal Journey */}
                <button
                    className={`mobile-nav-item ai-central ${currentPage === 'signal-journey' ? 'active' : ''}`}
                    onClick={() => onNavigate('signal-journey')}
                    title="Signal Journey"
                >
                    <div className="nav-icon-wrapper-large">
                        <span className="ai-logo-text">AI</span>
                    </div>
                </button>

                {/* Config */}
                <button
                    className={`mobile-nav-item ${currentPage === 'settings' ? 'active' : ''}`}
                    onClick={() => onNavigate('settings')}
                    title="Configurações"
                >
                    <div className="nav-icon-wrapper">
                        <IconSettings />
                    </div>
                </button>

                {/* Sair */}
                <button
                    className="mobile-nav-item"
                    onClick={onLogout}
                    title="Sair"
                >
                    <div className="nav-icon-wrapper">
                        <IconLogout />
                    </div>
                </button>
            </nav>

            {/* AI Submenu */}
            {showAIMenu && (
                <div className="mobile-submenu ai-submenu" ref={aiMenuRef}>
                    <button
                        className={`submenu-item ${currentPage === 'ai' ? 'active' : ''}`}
                        onClick={() => handleAIItemClick('ai')}
                    >
                        <IconAI />
                        <span>Auditoria IA</span>
                    </button>
                    <button
                        className={`submenu-item ${currentPage === 'ml' ? 'active' : ''}`}
                        onClick={() => handleAIItemClick('ml')}
                    >
                        <IconBrain />
                        <span>ML Performance</span>
                    </button>
                </div>
            )}

            {/* 10M Submenu */}
            {show10MMenu && (
                <div className="mobile-submenu tenm-submenu" ref={tenMMenuRef}>
                    {tenMMenuItems.map(item => (
                        <button
                            key={item.id}
                            className={`submenu-item ${currentPage === item.id ? 'active' : ''}`}
                            onClick={() => handle10MItemClick(item.id)}
                        >
                            {item.icon}
                            <span>{item.label}</span>
                        </button>
                    ))}
                </div>
            )}
        </>
    );
}
