import React from 'react';
import { IconDashboard, IconOrganizer, IconHistory, IconSettings, IconSun, IconMoon, IconLogout, IconAI } from './Icons';

export default function Sidebar({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const menuItems = [
        { id: 'dashboard', icon: <IconDashboard />, label: 'Dashboard' },
        { id: 'organizer', icon: <IconOrganizer />, label: 'Organizador' },
        { id: 'history', icon: <IconHistory />, label: 'Histórico' },
        { id: 'ai', icon: <IconAI />, label: 'Auditoria IA' },
        { id: 'settings', icon: <IconSettings />, label: 'Configurações' }
    ];

    return (
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
    );
}
