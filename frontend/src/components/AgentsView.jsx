import React, { useState, useEffect, useRef } from 'react';
import { Shield, Target, Cpu, MessageSquare, Zap, Activity, Globe, Compass, Brain, Terminal, Eye, Newspaper, Anchor } from 'lucide-react';
import './AgentsView.css';

export default function AgentsView() {
    const [agents, setAgents] = useState([]);
    const [llmStatus, setLlmStatus] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeAgent, setActiveAgent] = useState(null); // Track who is "speaking"
    const logsEndRef = useRef(null);

    // Fetches real logs from the new endpoint
    const fetchLogs = async () => {
        try {
            const res = await fetch('/api/system/logs');
            const data = await res.json();

            if (data.status === 'OK' && data.logs) {
                // Determine new logs to trigger animation
                const currentIds = new Set(logs.map(l => l.id));
                const newEntries = data.logs.filter(l => !currentIds.has(l.id));

                if (newEntries.length > 0) {
                    setLogs(data.logs);

                    // Trigger visual feedback for the latest agent
                    const latest = newEntries[newEntries.length - 1];
                    setActiveAgent(latest.agent);
                    setTimeout(() => setActiveAgent(null), 2000);
                } else if (logs.length === 0) {
                    // Initial load
                    setLogs(data.logs);
                }
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
        }
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
        fetchLogs(); // Initial fetch

        const interval = setInterval(fetchSystemState, 5000);
        const logInterval = setInterval(fetchLogs, 3000); // Poll logs every 3s

        return () => {
            clearInterval(interval);
            clearInterval(logInterval);
        };
    }, []);

    // FORCE DEMO ON LOAD (To satisfy user report of "nothing happening")
    useEffect(() => {
        const timer = setTimeout(() => {
            console.log("FORCE DEMO TRIGGERED");
            setActiveAgent('scout'); // Light up Scout
            setTimeout(() => setActiveAgent('bankroll_captain_agent'), 1500); // Then Captain
            setTimeout(() => setActiveAgent(null), 3000);
        }, 2000);
        return () => clearTimeout(timer);
    }, []);

    const getIcon = (id) => {
        switch (id) {
            case 'health_monitor': return <Activity size={20} />;
            case 'scout':
            case 'technical_agent': return <Target size={20} />;
            case 'sentinel':
            case 'fundamental_agent': return <Compass size={20} />;
            case 'strategist': return <Cpu size={20} />;
            case 'governor':
            case 'risk_agent': return <Shield size={20} className="text-warning" />;
            case 'anchor':
            case 'market_info_agent': return <Newspaper size={20} />;
            case 'ml_supervisor_agent': return <Eye size={20} className="text-cyan-400" />;
            case 'elite_manager':
            case 'bankroll_captain_agent': return <Anchor size={20} className="text-emerald-400" />;
            case 'gemini': return <Brain size={32} className="text-violet-400" />;
            default: return <Activity size={20} />;
        }
    };

    return (
        <div className="agents-view-v2 fade-in">
            {/* INJECTED STYLES TO BYPASS CACHE ISSUES */}
            <style>{`
                /* CORE LAYOUT */
                .agents-view-v2 {
                    background: radial-gradient(circle at center, #1a1f35 0%, #0f1320 100%) !important;
                    color: #e2e8f0 !important;
                    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                .neural-grid-container {
                    display: flex !important;
                    flex-direction: row !important;
                    flex: 1;
                    padding: 2rem;
                    gap: 2rem;
                    overflow: hidden;
                }

                /* AGENTS NETWORK (Left) */
                .agents-network {
                    flex: 2;
                    display: flex !important;
                    flex-direction: column !important;
                    justify-content: center;
                    align-items: center;
                    background-image: 
                        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px) !important;
                    background-size: 40px 40px !important;
                    border-radius: 1rem;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    position: relative;
                }

                /* CENTRAL BRAIN */
                .central-node {
                    display: flex !important;
                    flex-direction: column !important;
                    align-items: center;
                    margin-bottom: 3rem;
                    z-index: 10;
                    position: relative;
                }
                
                .brain-core {
                    width: 100px;
                    height: 100px;
                    background: rgba(139, 92, 246, 0.1);
                    border: 2px solid #8b5cf6;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 1rem;
                    box-shadow: 0 0 30px rgba(139, 92, 246, 0.3);
                    transition: all 0.5s ease;
                }
                
                .pulse-glow {
                    animation: brainPulse 3s infinite;
                    border-color: #a78bfa !important;
                    box-shadow: 0 0 40px rgba(139, 92, 246, 0.5) !important;
                }

                .brain-offline {
                    filter: grayscale(100%);
                    opacity: 0.5;
                    border-color: #475569 !important;
                    box-shadow: none !important;
                    animation: none !important;
                }
                
                @keyframes brainPulse {
                    0% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.2); transform: scale(1); }
                    50% { box-shadow: 0 0 60px rgba(139, 92, 246, 0.7); transform: scale(1.02); }
                    100% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.2); transform: scale(1); }
                }
                    font-size: 1.2rem !important;
                    font-weight: 800 !important;
                    color: #a78bfa !important;
                    letter-spacing: 1px !important;
                    text-transform: uppercase;
                }
                
                .brain-status {
                    font-size: 0.8rem;
                    color: #2dd4bf;
                    background: rgba(45, 212, 191, 0.1);
                    padding: 0.2rem 0.6rem;
                    border-radius: 1rem;
                    margin-top: 0.5rem;
                }

                /* SATELLITE GRID */
                .satellite-grid {
                    display: grid !important;
                    grid-template-columns: repeat(3, 1fr) !important;
                    gap: 2rem !important;
                    width: 100%;
                    max-width: 900px;
                }

                .agent-node {
                    display: flex !important;
                    align-items: center;
                    gap: 1rem;
                    background: rgba(30, 41, 59, 0.6) !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                    padding: 1rem;
                    border-radius: 0.8rem;
                    position: relative;
                }
                
                .node-icon-wrapper {
                    position: relative;
                    width: 48px;
                    height: 48px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #94a3b8;
                }
                
                .node-info h3 {
                    font-size: 1rem;
                    color: #f1f5f9;
                    margin: 0;
                    font-weight: bold;
                }
                
                .node-info .role {
                    font-size: 0.75rem;
                    color: #64748b;
                    margin: 0;
                }

                /* ANIMATIONS & BEAMS */
                .connection-beam {
                    position: absolute;
                    bottom: 50%;
                    left: 50%;
                    width: 2px;
                    height: 40px; /* Idle State: Short connection stub */
                    opacity: 0.2 !important; /* Always faintly visible */
                    transform: translateX(-50%);
                    z-index: 0;
                    pointer-events: none;
                    background: linear-gradient(to top, rgba(139,92,246,0.5), transparent);
                    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .connection-beam.firing {
                    height: 150px !important; /* Active State: Extend towards brain */
                    width: 4px;
                    opacity: 1 !important;
                    background: linear-gradient(to top, #8b5cf6, transparent);
                    box-shadow: 0 0 15px rgba(139, 92, 246, 0.6);
                    z-index: 9999;
                }
                .active-uplink {
                    border-color: #2dd4bf !important;
                    box-shadow: 0 0 20px rgba(45, 212, 191, 0.4) !important;
                    background: rgba(30, 41, 59, 1) !important;
                    transform: scale(1.05);
                    transition: all 0.3s ease;
                }
                
                /* WAR ROOM LOGS */
                .war-room-terminal {
                    flex: 1;
                    min-width: 300px;
                    background: #0f1117 !important;
                    border: 1px solid #334155;
                    border-radius: 0.8rem;
                    display: flex;
                    flex-direction: column;
                    font-family: 'JetBrains Mono', monospace !important;
                }
                .terminal-header {
                    background: #1e293b;
                    padding: 0.8rem;
                    color: #cbd5e1;
                    font-weight: bold;
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                }
                .terminal-body {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1rem;
                    gap: 0.5rem;
                    display: flex;
                    flex-direction: column;
                }
                .log-entry {
                    display: flex;
                    gap: 0.5rem;
                    line-height: 1.4;
                    font-size: 0.85rem;
                }
                .log-time { color: #475569; }
                .log-msg { color: #e2e8f0; }

                /* MOBILE RESPONSIVENESS */
                @media (max-width: 1024px) {
                    .neural-grid-container {
                        flex-direction: column !important;
                        overflow-y: auto !important;
                        padding: 1rem !important;
                    }
                    .agents-view-v2 {
                        height: auto !important;
                        overflow-y: auto !important;
                    }
                    .satellite-grid {
                        grid-template-columns: repeat(2, 1fr) !important;
                    }
                    .war-room-terminal {
                        min-height: 400px;
                    }
                }

                @media (max-width: 640px) {
                    .satellite-grid {
                        grid-template-columns: 1fr !important;
                    }
                    .neural-header h1 {
                        font-size: 1rem !important;
                    }
                    .war-room-terminal {
                        font-size: 0.75rem;
                    }
                }
            `}</style>

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
                        <div className={`brain-core ${!llmStatus?.llm_enabled ? 'brain-offline' :
                            activeAgent === 'gemini' ? 'active-uplink' : 'pulse-glow'
                            }`}>
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
                            <div key={agent.id} className={`agent-node ${agent.id} ${activeAgent === agent.id ? 'active-uplink' : ''}`}>
                                <div className="node-icon-wrapper">
                                    {getIcon(agent.id)}
                                    {/* Beam activates when agent is active */}
                                    <div className={`connection-beam ${activeAgent === agent.id ? 'firing' : ''}`}></div>
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
