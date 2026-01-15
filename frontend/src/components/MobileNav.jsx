import React from 'react'; // Force deploy update
import { IconDashboard, IconOrganizer, IconHistory, IconSun, IconMoon, IconLogout, IconAI } from './Icons';

export default function MobileNav({ currentPage, onNavigate, theme, onToggleTheme, onLogout }) {
    const menuItems = [
        { id: 'dashboard', icon: <IconDashboard />, label: 'Trades' },
        { id: 'organizer', icon: <IconOrganizer />, label: '10M' },
        { id: 'history', icon: <IconHistory />, label: 'History' },
        { id: 'ai', icon: <IconAI />, label: 'Auditoria' }
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
