import React, { useState, useEffect, useRef } from 'react';
import { IconDashboard, IconOrganizer, IconHistory, IconSettings, IconSun, IconMoon, IconLogout, IconAI, IconBrain } from './Icons';

export default function Sidebar({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const [showAIMenu, setShowAIMenu] = useState(false);
    const [showConfigMenu, setShowConfigMenu] = useState(false);
    const [show10MMenu, setShow10MMenu] = useState(false);
    const aiMenuRef = useRef(null);
    const configMenuRef = useRef(null);
    const tenMMenuRef = useRef(null);

    const menuItems = [
        { id: 'dashboard', icon: <IconDashboard />, label: 'Invest', mobileLabel: 'Invest' },
        { id: 'organizer', icon: <IconOrganizer />, label: 'Organizador', mobileLabel: '10M' },
        { id: 'history', icon: <IconHistory />, label: 'Histórico', mobileLabel: 'Histórico' },
    ];

    const aiMenuItems = [
        { id: 'ai', icon: <IconAI />, label: 'Auditoria IA' },
        { id: 'ml', icon: <IconBrain />, label: 'ML Performance' },
    ];

    const tenMMenuItems = [
        { id: 'organizer', icon: <IconOrganizer />, label: 'Organizador de Tarefas' },
        { id: 'history', icon: <IconHistory />, label: 'Histórico' },
    ];

    // Close menus when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (aiMenuRef.current && !aiMenuRef.current.contains(event.target)) {
                setShowAIMenu(false);
            }
            if (configMenuRef.current && !configMenuRef.current.contains(event.target)) {
                setShowConfigMenu(false);
            }
            if (tenMMenuRef.current && !tenMMenuRef.current.contains(event.target)) {
                setShow10MMenu(false);
            }
        };

        if (showAIMenu || showConfigMenu || show10MMenu) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showAIMenu, showConfigMenu, show10MMenu]);

    const handleAIClick = () => {
        setShowAIMenu(!showAIMenu);
        setShowConfigMenu(false);
        setShow10MMenu(false);
    };

    const handleConfigClick = () => {
        setShowConfigMenu(!showConfigMenu);
        setShowAIMenu(false);
        setShow10MMenu(false);
    };

    const handle10MClick = () => {
        setShow10MMenu(!show10MMenu);
        setShowAIMenu(false);
        setShowConfigMenu(false);
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
                        className="nav-item"
                        onClick={handleConfigClick}
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
            {(showAIMenu || showConfigMenu || show10MMenu) && (
                <div
                    className="mobile-submenu-backdrop"
                    onClick={() => {
                        setShowAIMenu(false);
                        setShowConfigMenu(false);
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
                    className={`mobile-nav-item ${(currentPage === 'organizer' || currentPage === 'history' || show10MMenu) ? 'active' : ''}`}
                    onClick={handle10MClick}
                    title="10M"
                >
                    <div className="nav-icon-wrapper">
                        <IconOrganizer />
                    </div>
                </button>

                {/* AI - Central Destacado */}
                <button
                    className={`mobile-nav-item ai-central ${(currentPage === 'ai' || currentPage === 'ml' || showAIMenu) ? 'active' : ''}`}
                    onClick={handleAIClick}
                    title="AI"
                >
                    <div className="nav-icon-wrapper-large">
                        <span className="ai-logo-text">AI</span>
                    </div>
                </button>

                {/* Config */}
                <button
                    className={`mobile-nav-item ${showConfigMenu ? 'active' : ''}`}
                    onClick={handleConfigClick}
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
                    <button
                        className={`submenu-item ${currentPage === 'organizer' ? 'active' : ''}`}
                        onClick={() => handle10MItemClick('organizer')}
                    >
                        <IconOrganizer />
                        <span>Organizador de Tarefas</span>
                    </button>
                    <button
                        className={`submenu-item ${currentPage === 'history' ? 'active' : ''}`}
                        onClick={() => handle10MItemClick('history')}
                    >
                        <IconHistory />
                        <span>Histórico</span>
                    </button>
                </div>
            )}

            {/* Config Submenu */}
            {showConfigMenu && (
                <div className="mobile-submenu config-submenu" ref={configMenuRef}>
                    <button
                        className="submenu-item"
                        onClick={() => {
                            onToggleTheme();
                            setShowConfigMenu(false);
                        }}
                    >
                        {theme === 'dark' ? <IconSun /> : <IconMoon />}
                        <span>{theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}</span>
                    </button>
                    {/* Adicionar mais opções de config aqui no futuro */}
                </div>
            )}
        </>
    );
}
