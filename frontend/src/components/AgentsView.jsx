import React, { useState, useEffect, useRef } from 'react';
import { Shield, Target, Cpu, MessageSquare, Zap, Activity, Globe, Compass, Brain, Terminal } from 'lucide-react';
import './AgentsView.css';

export default function AgentsView() {
    const [agents, setAgents] = useState([]);
    const [llmStatus, setLlmStatus] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const logsEndRef = useRef(null);

    // Mock logs generator for "War Room" feel (until backend is fully event-driven)
    const generateMockLog = (agentList) => {
        if (!agentList || agentList.length === 0) return null;

        const actions = [
            { agent: 'scout', msg: '👁️ Varredura de 30 pares concluída. Padrão bullish em SOL.' },
            { agent: 'sentinel', msg: '🛡️ Volume institucional detectado em BTC. Absorção confirmada.' },
            { agent: 'strategist', msg: '🧠 Correlação BTC/ETH estável (0.85). Cenário favorável.' },
            { agent: 'governor', msg: '⚖️ Risco da banca em 12%. Autorizando novos slots.' },
            { agent: 'anchor', msg: '⚓ SP500 abrindo em alta. Contexto macro: RISK-ON.' },
            { agent: 'elite_manager', msg: '🦅 Monitorando 2 posições abertas. Trailing stop ativo.' },
            { agent: 'gemini', msg: '💡 CORTEX: Validando sinal com 89% de confiança. Proceder.' }
        ];

        const randomAction = actions[Math.floor(Math.random() * actions.length)];
        return {
            id: Date.now(),
            timestamp: new Date().toLocaleTimeString(),
            agent: randomAction.agent,
            message: randomAction.msg
        };
    };

    const fetchSystemState = async () => {
        try {
            // Fetch Agents
            const agentsRes = await fetch('/api/system/agents');
            const agentsData = await agentsRes.json();

            // Fetch LLM Status
            const llmRes = await fetch('/api/llm/status');
            const llmData = await llmRes.json();

            if (agentsData.status === 'OK') {
                setAgents(agentsData.agents);
            }
            if (llmData.status === 'OK') {
                setLlmStatus(llmData);
            }

            setLoading(false);

        } catch (error) {
            console.error('Error fetching system state:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSystemState();
        const interval = setInterval(fetchSystemState, 5000);

        // Simulate Live Logs
        const logInterval = setInterval(() => {
            const newLog = generateMockLog(agents);
            if (newLog) {
                setLogs(prev => [...prev.slice(-50), newLog]); // Keep last 50 logs
            }
        }, 3500);

        return () => {
            clearInterval(interval);
            clearInterval(logInterval);
        };
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const getIcon = (id) => {
        switch (id) {
            case 'health_monitor': return <Activity size={20} />;
            case 'scout': return <Target size={20} />;
            case 'sentinel': return <Compass size={20} />;
            case 'strategist': return <Cpu size={20} />;
            case 'governor': return <Shield size={20} className="text-warning" />;
            case 'anchor': return <Globe size={20} />;
            case 'elite_manager': return <Zap size={20} className="text-emerald-400" />;
            case 'gemini': return <Brain size={32} className="text-violet-400" />;
            default: return <Activity size={20} />;
        }
    };

    return (
        <div className="agents-view-v2 fade-in">
            <header className="neural-header">
                <div className="header-content">
                    <h1>NEURAL COMMAND CENTER</h1>
                    <div className="live-indicator">
                        <span className="blink">●</span> SYSTEM ONLINE
                    </div>
                </div>
            </header>

            <div className="neural-grid-container">

                {/* LEFT: THE AGENTS GRID */}
                <div className="agents-network">
                    {/* CENTRAL BRAIN (GEMINI) */}
                    <div className="central-node">
                        <div className="brain-core pulse-glow">
                            {getIcon('gemini')}
                        </div>
                        <div className="brain-label">GEMINI 1.5 CORTEX</div>
                        <div className="brain-status">
                            {llmStatus?.llm_enabled ? 'CONNECTED' : 'OFFLINE'}
                        </div>

                        {/* CONNECTION LINES (SVG OVERLAY WOULD GO HERE, SIMULATED VIA CSS FOR NOW) */}
                        <div className="connection-lines"></div>
                    </div>

                    {/* SATELLITE AGENTS */}
                    <div className="satellite-grid">
                        {agents.map(agent => (
                            <div key={agent.id} className={`agent-node ${agent.id}`}>
                                <div className="node-icon-wrapper">
                                    {getIcon(agent.id)}
                                    <div className="connection-beam"></div>
                                </div>
                                <div className="node-info">
                                    <h3>{agent.name}</h3>
                                    <p className="role">{agent.role}</p>
                                    <div className="mini-status">{agent.last_action}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* RIGHT: THE WAR ROOM (LOGS) */}
                <div className="war-room-terminal">
                    <div className="terminal-header">
                        <Terminal size={16} />
                        <span>NEURAL_STREAM_LOGS // v.3.0</span>
                    </div>
                    <div className="terminal-body">
                        {logs.map(log => (
                            <div key={log.id} className="log-entry">
                                <span className="log-time">[{log.timestamp}]</span>
                                <span className={`log-agent ${log.agent}`}>{log.agent.toUpperCase()}:</span>
                                <span className="log-msg">{log.message}</span>
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                    <div className="terminal-input">
                        <span className="prompt">{'>'}</span>
                        <span className="cursor">_</span>
                    </div>
                </div>

            </div>
        </div>
    );
}
