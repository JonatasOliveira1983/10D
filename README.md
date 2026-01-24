# 10D Trading System v6.5 (The Autonomous Update)

**10D** is an advanced automated trading system powered by Hybrid Intelligence (Rule-Based Scanners + Multi-Agent LLM Council) to identify high-probability crypto setups and manage capital with institutional-grade precision.

## 🚀 Status: OPERATIONAL
- **Frontend**: "Neural Interface" Dashboard (React + Tailwind) - **PORT 3001**
- **Backend**: Flask API + Python + Supabase - **PORT 5002**
- **AI Core**: Council of Agents (Gemini 2.0 Cortex)
- **ML Core**: Autonomous Model Care (Random Forest)

## 🧠 Inteligência Híbrida: O Conselho de Agentes
O sistema evoluiu para uma estrutura de **Autonomia Total**, onde os agentes não apenas sugerem, mas gerenciam ativamente o ciclo de vida do capital e dos modelos:

1.  **Bankroll Captain (General)**: O mestre tático. Gerencia os 10 slots de elite, executa saídas por Fibonacci, confirma reversões com Price Action e realiza "Smart Flips".
2.  **ML Supervisor Agent (Model Care)**: Gerente autônomo do Machine Learning. Coleta dados "Journey" em tempo real e dispara retreinos em background assim que o limite de amostras é atingido.
3.  **Market Info Agent**: Monitora notícias em tempo real (Bybit/RSS) e fornece o contexto macro para o conselho.
4.  **Soldados (Scout & Sentinel)**: Monitoramento especializado de tendências MTF e caça de liquidez (CVD/LSR).

## 💎 Funcionalidades de Elite (v6.5)

### 1. Tática Fibonacci & Smart Flip
- **Fib Exit**: Saída automática em níveis de retração de 50% (0.5 Fib) para proteger lucros explosivos (>100% ROI).
- **Price Action Confirmation**: Saídas validadas por padrões de candle (Hammer, Shooting Star, Engulfing).
- **Smart Reversal**: Inversão de mão tática no nível 0.5 para lucrar na correção e na continuação do movimento.

### 2. Gestão de slots e Inércia
- **Otimização de Slots**: Liberação automática de slots para moedas em estagnação (100-300% ROI há mais de 6h).
- **Escudo BTC & Pânico**: Proteção global da banca em caso de quedas bruscas do mercado.

### 3. M.L Autônomo e Fluxo Não-Bloqueante
- **Warmup Inteligente**: O gerador de sinais opera em modo fallback (Journey) enquanto o modelo ML está sendo treinado, garantindo que o sistema nunca fique parado.
- **Model Care Heartbeat**: Monitoramento estatístico contínuo da acurácia e precisão do modelo.

### 4. Neural Interface & HUD Tático
- **Agent Detail Cards**: Clique nos agentes no HUD para ver telemetria detalhada e "pensamentos" em tempo real.
- **Mobile Optimized**: Dashboard preparado para monitoramento e intervenção tática via celular.

## 🛠️ Execução do Sistema

### 1. Backend (Python/Flask)
```bash
python backend/app.py
```

### 2. Frontend (React/Vite)
```bash
cd frontend
npm run dev
```

---
*Atualizado em: 24/01/2026 - Versão 6.5 (The Autonomous Update)*
