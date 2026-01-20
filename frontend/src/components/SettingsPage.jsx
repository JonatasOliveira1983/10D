import React from 'react';
import { useTranslation } from 'react-i18next';
import { IconSettings, IconGlobe, IconPalette, IconSun, IconMoon } from './Icons';
import './SettingsPage.css';

const languages = [
    { code: 'pt-BR', name: 'Português', abbr: 'PT' },
    { code: 'en', name: 'English', abbr: 'EN' },
    { code: 'es', name: 'Español', abbr: 'ES' }
];

export default function SettingsPage({ theme, onToggleTheme }) {
    const { t, i18n } = useTranslation();

    const currentLanguage = i18n.language;

    const handleLanguageChange = (langCode) => {
        i18n.changeLanguage(langCode);
    };

    return (
        <div className="settings-page">
            <h1 className="settings-title">
                <IconSettings size={28} className="title-icon" />
                {t('settings.title')}
            </h1>

            <div className="settings-section">
                <h2 className="section-title">
                    <IconGlobe size={20} className="section-icon" />
                    {t('settings.language')}
                </h2>
                <div className="language-options">
                    {languages.map(lang => (
                        <button
                            key={lang.code}
                            className={`language-option ${currentLanguage === lang.code ? 'active' : ''}`}
                            onClick={() => handleLanguageChange(lang.code)}
                        >
                            <span className="lang-abbr">{lang.abbr}</span>
                            <span className="lang-name">{lang.name}</span>
                            {currentLanguage === lang.code && (
                                <span className="check-mark">✓</span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            <div className="settings-section">
                <h2 className="section-title">
                    <IconPalette size={20} className="section-icon" />
                    {t('settings.theme')}
                </h2>
                <div className="theme-options">
                    <button
                        className={`theme-option ${theme === 'dark' ? 'active' : ''}`}
                        onClick={() => theme !== 'dark' && onToggleTheme()}
                    >
                        <div className="theme-icon-box">
                            <IconMoon size={24} />
                        </div>
                        <span className="theme-name">{t('settings.dark')}</span>
                        {theme === 'dark' && <span className="check-mark">✓</span>}
                    </button>
                    <button
                        className={`theme-option ${theme === 'light' ? 'active' : ''}`}
                        onClick={() => theme !== 'light' && onToggleTheme()}
                    >
                        <div className="theme-icon-box">
                            <IconSun size={24} />
                        </div>
                        <span className="theme-name">{t('settings.light')}</span>
                        {theme === 'light' && <span className="check-mark">✓</span>}
                    </button>
                </div>
            </div>
        </div>
    );
}
