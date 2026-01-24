# 10D Trading System v6.0 (The Council Update)

**10D** is an advanced automated trading system powered by Hybrid Intelligence (Rule-Based Scanners + Multi-Agent LLM Council) to identify high-probability crypto setups and manage capital with institutional-grade precision.

## 🚀 Status: OPERATIONAL
- **Frontend**: "Neural Interface" Dashboard (React + Tailwind) - **PORT 3001**
- **Backend**: Flask API + Python + Supabase - **PORT 5002**
- **AI Core**: Council of Agents (Gemini 1.5 Cortex)

## 🧠 Inteligência Híbrida: O Conselho de Agentes
O sistema evoluiu de uma estrutura linear para um **Conselho Deliberativo**, onde múltiplos agentes especializados colaboram:

1.  **Market Info Agent**: Monitora notícias globais, listagens em exchanges e sentimento macro para fornecer contexto fundamental.
2.  **ML Supervisor Agent**: Monitora a performance dos modelos de Machine Learning em tempo real, ajustando pesos ou alertando sobre anomalias.
3.  **Bankroll Captain (General)**: O tomador de decisão final. Ele recebe os dossiês dos outros agentes e executa a gestão de risco estrita.
4.  **Soldados (Scout & Sentinel)**: Scanners matemáticos de alta velocidade que filtram 200+ pares para o Conselho analisar.

## 💎 Funcionalidades Premium (v6.0)

### 1. Gestão de Banca 10-Slot (Escala Dinâmica)
A lógica de risco foi aprimorada para maximizar o ROI sem expor o capital excessivamente:
- **Limite de Risco**: Máximo de 20% da banca total em risco simultâneo.
- **Configuração de Slots**: Dividido em até **10 slots simultâneos**.
- **Entradas Inteligentes**: Cada entrada ocupa 2% a 5% da banca, dependendo da confiança do Conselho.
- **Reciclagem de Capital**: Assim que um trade atinge o "Risk-Free" (Break Even), o slot é liberado para novas operações.

### 2. M.L Máquina de Aprendizado (Nova Interface)
- **Dashboard Dedicado**: Visualização clara de métricas de treinamento, acurácia e logs técnicos do Supervisor de ML.
- **Remoção de Ruído**: As páginas de ML agora focam puramente em performance preditiva, separando dados operacionais de dados técnicos.

### 3. Neural Interface & HUD Tático
- **Agent HUD**: Visualização em tempo real do "pensamento" dos agentes durante a análise de sinais.
- **Tactical Charts**: Linhas de Stop-Loss e Take-Profit dinâmicas integradas ao gráfico da "Banca".
- **Mobile First**: Interface otimizada para monitoramento via smartphone.

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

## ⚠️ Troubleshooting

### "Logs não aparecem"
Verifique a conectividade com o Supabase e se o Buffer de Memória está ativo na porta 5002.

### "Interface Antiga"
O sistema utiliza Service Workers para performance. Se necessário, force a limpeza de cache com **Ctrl + F5**.

---
*Atualizado em: 24/01/2026 - Versão 6.0 (The Council Update)*
