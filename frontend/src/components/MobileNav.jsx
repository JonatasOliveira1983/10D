import React from 'react';
import { IconDashboard, IconOrganizer, IconHistory, IconSettings, IconSun, IconMoon, IconLogout } from './Icons';

export default function MobileNav({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const menuItems = [
        { id: 'dashboard', icon: <IconDashboard size={20} />, label: 'Dash' },
        { id: 'organizer', icon: <IconOrganizer size={20} />, label: 'Plan' },
        { id: 'history', icon: <IconHistory size={20} />, label: 'Hist' },
    ];

    return (
        <nav className="mobile-nav">
            {menuItems.map(item => (
                <button
                    key={item.id}
                    className={`mobile-nav-item ${currentPage === item.id ? 'active' : ''}`}
                    onClick={() => onNavigate(item.id)}
                >
                    <div className="nav-icon-wrapper mobile">
                        {item.icon}
                    </div>
                    <span className="nav-label">{item.label}</span>
                </button>
            ))}

            <button
                className="mobile-nav-item"
                onClick={onToggleTheme}
            >
                <div className="nav-icon-wrapper mobile">
                    {theme === 'dark' ? <IconSun size={20} /> : <IconMoon size={20} />}
                </div>
                <span className="nav-label">Tema</span>
            </button>

            <button
                className="mobile-nav-item"
                onClick={onLogout}
            >
                <div className="nav-icon-wrapper mobile">
                    <IconLogout size={20} />
                </div>
                <span className="nav-label">Sair</span>
            </button>
        </nav>
    );
}
