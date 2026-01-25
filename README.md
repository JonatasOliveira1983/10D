# 10D Trading System v6.6 (Elite & Risk Update)

**10D** is an advanced automated trading system powered by Hybrid Intelligence (Rule-Based Scanners + Multi-Agent LLM Council) to identify high-probability crypto setups and manage capital with institutional-grade precision.

## 🚀 Status: OPERATIONAL (TESTNET)
- **Frontend**: "Neural Interface" Dashboard (React + Tailwind) - **PORT 3001**
- **Backend**: Flask API + Python + Supabase - **PORT 5002**
- **Testnet**: Connected to Bybit Testnet via `api-testnet.bybit.com`
- **Environment**: Authenticated with HMAC keys.

## 🧠 Inteligência Híbrida: O Conselho de Agentes
O sistema evoluiu para uma estrutura de **Autonomia Total**, onde os agentes não apenas sugerem, mas gerenciam ativamente o ciclo de vida do capital e dos modelos:

1.  **Bankroll Captain (General)**: O mestre tático. Gerencia os 10 slots de elite, enforce 20% max exposure e executa ordens no Testnet.
2.  **ML Supervisor Agent (Model Care)**: Gerente autônomo do Machine Learning. Coleta dados "Journey" em tempo real e dispara retreinos em background.
3.  **Market Info Agent**: Monitora notícias em tempo real (Bybit/RSS) e fornece o contexto macro para o conselho.
4.  **Soldados (Scout & Sentinel)**: Monitoramento especializado de tendências MTF e caça de liquidez (CVD/LSR).

## 💎 Funcionalidades de Elite (v6.6)

### 1. Gestão de Risco & Slots
- **20% Exposure Cap**: Proteção rígida que limita cada operação a no máximo 20% do capital unificado.
- **10 Active Slots**: Limite de 10 operações simultâneas para garantir foco e liquidez.
- **Risk UI Header**: HUD visual em tempo real no dashboard da Banca mostrando slots ocupados e teto de risco.

### 2. Sinais Elite (Standardized)
- **Score >= 65**: Apenas sinais com pontuação técnica robusta são considerados.
- **MTF Confluence**: Exige confirmação em múltiplos timeframes (Eagle Elite logic).

---
*Atualizado em: 25/01/2026 - Versão 6.6 (Elite & Risk Update)*
