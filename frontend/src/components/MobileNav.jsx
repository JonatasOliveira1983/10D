import React from 'react';

export default function MobileNav({ currentPage, onNavigate, theme, onToggleTheme }) {
    const menuItems = [
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { id: 'history', icon: '📜', label: 'Histórico' },
        { id: 'settings', icon: '⚙️', label: 'Config' }
    ];

    return (
        <nav className="mobile-nav">
            {menuItems.map(item => (
                <button
                    key={item.id}
                    className={`mobile-nav-item ${currentPage === item.id ? 'active' : ''}`}
                    onClick={() => onNavigate(item.id)}
                >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                </button>
            ))}

            <button
                className="mobile-nav-item"
                onClick={onToggleTheme}
            >
                <span className="nav-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
                <span className="nav-label">Tema</span>
            </button>
        </nav>
    );
}
