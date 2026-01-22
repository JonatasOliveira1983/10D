import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { IconDashboard, IconOrganizer, IconHistory, IconSettings, IconSun, IconMoon, IconLogout, IconAI, IconBrain } from './Icons';

export default function Sidebar({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const { t } = useTranslation();
    const [showMLMenu, setShowMLMenu] = useState(false);
    const [show10MMenu, setShow10MMenu] = useState(false);
    const mlMenuRef = useRef(null);
    const tenMMenuRef = useRef(null);

    const menuItems = [
        { id: 'dashboard', icon: <IconBrain />, label: t('nav.invest'), mobileLabel: 'M.L' },
        { id: 'signal-journey', icon: <IconBrain />, label: t('nav.signalJourney'), mobileLabel: 'Journey' },
        { id: 'journey-history', icon: <IconHistory />, label: t('nav.journeyHistory'), mobileLabel: 'Histórico' },
        { id: 'agents', icon: <IconAI />, label: 'Agentes', mobileLabel: 'Agentes' },
        { id: 'banca', icon: <IconOrganizer />, label: 'Banca', mobileLabel: 'Banca' },
    ];

    // Close menus when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (mlMenuRef.current && !mlMenuRef.current.contains(event.target)) {
                setShowMLMenu(false);
            }
            if (tenMMenuRef.current && !tenMMenuRef.current.contains(event.target)) {
                setShow10MMenu(false);
            }
        };

        if (showMLMenu || show10MMenu) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showMLMenu, show10MMenu]);

    const handleMLClick = () => {
        setShowMLMenu(!showMLMenu);
        setShow10MMenu(false);
        if (!showMLMenu) onNavigate('dashboard');
    };

    const handle10MClick = () => {
        setShow10MMenu(!show10MMenu);
        setShowMLMenu(false);
        if (!show10MMenu) onNavigate('banca');
    };

    const handleMLItemClick = (id) => {
        onNavigate(id);
        setShowMLMenu(false);
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

                    <div className="sidebar-divider" style={{ margin: '1rem 0', borderTop: '1px solid rgba(255,255,255,0.05)' }}></div>

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
            {(showMLMenu || show10MMenu) && (
                <div
                    className="mobile-submenu-backdrop"
                    onClick={() => {
                        setShowMLMenu(false);
                        setShow10MMenu(false);
                    }}
                />
            )}

            {/* Mobile Bottom Navigation */}
            <nav className="mobile-nav">
                {/* ML Máquina de Aprendizado */}
                <button
                    className={`mobile-nav-item ${(currentPage === 'dashboard' || currentPage === 'signal-journey' || currentPage === 'journey-history' || showMLMenu) ? 'active' : ''}`}
                    onClick={handleMLClick}
                    title="M.L Máquina"
                >
                    <div className="nav-icon-wrapper">
                        <IconBrain />
                    </div>
                </button>

                {/* Banca */}
                <button
                    className={`mobile-nav-item ${currentPage === 'banca' ? 'active' : ''}`}
                    onClick={() => onNavigate('banca')}
                    title="Banca"
                >
                    <div className="nav-icon-wrapper">
                        <IconOrganizer />
                    </div>
                </button>

                {/* AI - Central Destacado - Agentes */}
                <button
                    className={`mobile-nav-item ai-central ${currentPage === 'agents' ? 'active' : ''}`}
                    onClick={() => onNavigate('agents')}
                    title="Agentes"
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

            {/* ML Submenu (Mobile) */}
            {showMLMenu && (
                <div className="mobile-submenu ml-submenu" ref={mlMenuRef}>
                    <button
                        className={`submenu-item ${currentPage === 'dashboard' ? 'active' : ''}`}
                        onClick={() => handleMLItemClick('dashboard')}
                    >
                        <IconBrain />
                        <span>M.L Máquina</span>
                    </button>
                    <button
                        className={`submenu-item ${currentPage === 'signal-journey' ? 'active' : ''}`}
                        onClick={() => handleMLItemClick('signal-journey')}
                    >
                        <IconBrain />
                        <span>Signal Journey</span>
                    </button>
                    <button
                        className={`submenu-item ${currentPage === 'journey-history' ? 'active' : ''}`}
                        onClick={() => handleMLItemClick('journey-history')}
                    >
                        <IconHistory />
                        <span>Histórico Journey</span>
                    </button>
                </div>
            )}
        </>
    );
}
