import React, { useState, useEffect } from 'react';
import { Shield, Target, Cpu, MessageSquare, Zap, Activity, Globe, Compass } from 'lucide-react';
import './AgentsView.css';

export default function AgentsView() {
    const [agents, setAgents] = useState([]);
    const [councilDebate, setCouncilDebate] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchAgents = async () => {
        try {
            const response = await fetch('/api/system/agents');
            const data = await response.json();
            if (data.status === 'OK') {
                setAgents(data.agents);
                setCouncilDebate(data.council_debate);
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
            case 'elite_manager': return <Zap size={24} className="text-emerald-400" />;
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

                            {agent.id === 'elite_manager' && agent.learning && (
                                <div className="agent-thought elite">
                                    <div className="thought-header">
                                        <Zap size={16} />
                                        <span>Status de Sniper</span>
                                    </div>
                                    <div className="elite-stats">
                                        <div className="stat-row">
                                            <span>XP: {agent.learning.experience_points}</span>
                                            <span className="strategy">{agent.learning.current_strategy}</span>
                                        </div>
                                        <div className="xp-bar">
                                            <div className="xp-fill" style={{ width: `${(agent.learning.experience_points % 100)}%` }}></div>
                                        </div>
                                    </div>
                                    <p className="elite-reflection">{agent.learning.last_reflection}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* COUNCIL DEBATE AUDIT SECTION */}
            {councilDebate && (
                <div className="council-audit-section fade-in">
                    <div className="audit-header">
                        <MessageSquare size={24} className="text-violet-400" />
                        <h2>Última Deliberação do Conselho</h2>
                        <span className="audit-badge">Auditoria em Tempo Real</span>
                    </div>

                    <div className="debate-grid">
                        <div className="debate-transcript">
                            <div className="transcript-header">Razão da Decisão: {councilDebate.approved ? '✅ Aprovado' : '❌ Rejeitado'}</div>
                            <p className="reasoning-text">"{councilDebate.reasoning}"</p>
                            <div className="confidence-meter">
                                <span>Confiança do Conselho</span>
                                <div className="meter-bar">
                                    <div className="meter-fill" style={{ width: `${councilDebate.confidence * 100}%` }}></div>
                                </div>
                                <span className="conf-pct">{(councilDebate.confidence * 100).toFixed(0)}%</span>
                            </div>
                        </div>

                        <div className="votes-summary">
                            <h3>Votos Individuais</h3>
                            <div className="votes-list">
                                {councilDebate.vote_breakdown && Object.entries(councilDebate.vote_breakdown).map(([agent, verdict]) => (
                                    <div key={agent} className="agent-vote">
                                        <span className="agent-name">{agent.toUpperCase()}</span>
                                        <span className={`vote-tag ${verdict === 'APPROVED' ? 'approved' : 'rejected'}`}>
                                            {verdict === 'APPROVED' ? 'Sim' : 'Não'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="agents-footer">
                <p>Os agentes utilizam LLM Gemini para processamento de linguagem natural e ajustes estratégicos constantes.</p>
            </div>
        </div>
    );
}
