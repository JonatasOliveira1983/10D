import React, { useState, useEffect } from 'react';

const OpeningPage = ({ onEnter }) => {
    const [isVisible, setIsVisible] = useState(true);

    const handleEnter = () => {
        setIsVisible(false);
        setTimeout(onEnter, 800); // Match transition duration
    };

    return (
        <div className={`opening-page ${!isVisible ? 'app-transition-exit' : ''}`}>
            <div className="opening-content">
                <h1 className="opening-main-title">Só Hoje</h1>

                <p className="opening-quote">
                    “Ao vencedor darei o direito de sentar-se comigo em meu trono,
                    assim como eu também venci e sentei-me com meu Pai em seu trono.”
                </p>
                <span className="opening-author">Apocalipse 3:21</span>

                <div className="opening-affirmations">
                    <p className="affirmation-text">Eu posso, eu consigo, eu mereço.</p>
                </div>

                <p className="opening-footer-quote">
                    "Onde há foco, há coerência vibracional"
                </p>

                <button className="btn-enter" onClick={handleEnter}>
                    Entrar
                </button>
            </div>
        </div>
    );
};

export default OpeningPage;
