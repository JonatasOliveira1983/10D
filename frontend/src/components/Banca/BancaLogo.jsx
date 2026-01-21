
import React from 'react';

const BancaLogo = ({ width = 64, height = 64, className = '' }) => {
    return (
        <svg
            width={width}
            height={height}
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={className}
        >
            <defs>
                <linearGradient id="eagleGradient" x1="50" y1="0" x2="50" y2="100" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#00ff88" />
                    <stop offset="100%" stopColor="#00cc6a" />
                </linearGradient>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>

            {/* Circle Container */}
            <circle cx="50" cy="50" r="48" stroke="url(#eagleGradient)" strokeWidth="2" strokeOpacity="0.3" fill="none" />
            <circle cx="50" cy="50" r="38" stroke="url(#eagleGradient)" strokeWidth="1" strokeOpacity="0.1" fill="none" />

            {/* Stylized Eagle Shape */}
            <path
                d="M50 20C50 20 25 40 20 60C18 68 25 75 35 70L50 60L65 70C75 75 82 68 80 60C75 40 50 20 50 20Z"
                fill="url(#eagleGradient)"
                filter="url(#glow)"
                opacity="0.9"
            />
            <path
                d="M50 25C50 25 30 45 28 58C28 58 35 65 50 55L65 65C65 65 72 58 72 58C70 45 50 25 50 25Z"
                fill="#0a0a0b"
            />
            <path
                d="M50 35L40 50L50 55L60 50L50 35Z"
                fill="url(#eagleGradient)"
            />
        </svg>
    );
};

export default BancaLogo;
