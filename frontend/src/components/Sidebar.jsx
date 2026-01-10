import React from 'react';

export default function Sidebar({ currentPage, onNavigate, theme, onToggleTheme }) {
    const menuItems = [
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { id: 'organizer', icon: '📁', label: 'Organizador' },
        { id: 'history', icon: '📜', label: 'Histórico' },
        { id: 'settings', icon: '⚙️', label: 'Configurações' }
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
                        <span className="nav-icon">{item.icon}</span>
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
                    <span className="theme-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
                </button>
            </div>
        </aside>
    );
}
