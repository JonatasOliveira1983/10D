import React, { useState, useEffect } from 'react';
import { Shield, Target, Cpu, MessageSquare, Zap, Activity, Globe, Compass } from 'lucide-react';
import './AgentsView.css';

export default function AgentsView() {
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchAgents = async () => {
        try {
            const response = await fetch('/api/system/agents');
            const data = await response.json();
            if (data.status === 'OK') {
                setAgents(data.agents);
                setLastUpdate(new Date().toLocaleTimeString());
            }
            setLoading(false);
        } catch (error) {
            console.error('Error fetching agents:', error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAgents();
        const interval = setInterval(fetchAgents, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const getIcon = (id) => {
        switch (id) {
            case 'health_monitor': return <Shield size={24} />;
            case 'scout': return <Target size={24} />;
            case 'sentinel': return <Compass size={24} />;
            case 'strategist': return <Cpu size={24} />;
            case 'governor': return <Shield size={24} className="text-warning" />;
            case 'anchor': return <Globe size={24} />;
            default: return <Activity size={24} />;
        }
    };

    return (
        <div className="agents-view fade-in">
            <div className="agents-header">
                <div className="title-group">
                    <h1>Rede Neural de Agentes</h1>
                    <p className="subtitle">Monitoramento em tempo real do ecossistema de inteligência 10D</p>
                </div>
                <div className="status-badge">
                    <span className="pulse"></span>
                    Última Reflexão: {lastUpdate}
                </div>
            </div>

            {loading ? (
                <div className="loading-container">
                    <Zap size={48} className="spin" />
                    <p>Sincronizando Rede Neural...</p>
                </div>
            ) : (
                <div className="agents-grid">
                    {agents.map(agent => (
                        <div key={agent.id} className="agent-card">
                            <div className="agent-card-header">
                                <div className="agent-icon">{getIcon(agent.id)}</div>
                                <div className="agent-info">
                                    <h3>{agent.name}</h3>
                                    <span className={`status-tag ${agent.status.toLowerCase()}`}>
                                        {agent.status}
                                    </span>
                                </div>
                            </div>

                            <div className="agent-role">
                                <label>Missão:</label>
                                <p>{agent.role}</p>
                            </div>

                            <div className="agent-last-action">
                                <label>Atividade Recente:</label>
                                <p>{agent.last_action}</p>
                            </div>

                            {agent.id === 'strategist' && agent.report && (
                                <div className="agent-thought">
                                    <div className="thought-header">
                                        <MessageSquare size={16} />
                                        <span>Último Post-Mortem</span>
                                    </div>
                                    <p>{agent.report.advice || "Analisando histórico de performance..."}</p>
                                    {agent.report.performance_grade && (
                                        <div className="grade-badge">Nota: {agent.report.performance_grade}</div>
                                    )}
                                </div>
                            )}

                            {agent.id === 'anchor' && agent.context && (
                                <div className="agent-thought macro">
                                    <div className="thought-header">
                                        <Globe size={16} />
                                        <span>Sentimento Global</span>
                                    </div>
                                    <div className="macro-stats">
                                        <span>{agent.context.global_sentiment}</span>
                                        <span className="multiplier">Conf: x{agent.context.confidence_multiplier}</span>
                                    </div>
                                    <p className="macro-summary">{agent.context.summary}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <div className="agents-footer">
                <p>Os agentes utilizam LLM Gemini para processamento de linguagem natural e ajustes estratégicos constantes.</p>
            </div>
        </div>
    );
}
