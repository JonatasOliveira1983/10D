# 🚀 10D - Sistema de Sinais de Trading com IA (v5.0 Stable)

Sistema avançado de análise e geração de sinais para criptomoedas que monitora os **top 100 pares da Bybit** em tempo real, utilizando estratégias técnicas filtradas por tendência, **Machine Learning Autônomo** e uma **Simulação de Banca Integradada (The Bankroll)**.

---

## 📊 Diagrama do Sistema

![System Flow Diagram](C:/Users/spcom/.gemini/antigravity/brain/33428682-b703-452a-81e2-7793345a2290/system_flow_diagram_1768441484224.png)

---

## 🔄 Fluxo Completo do Sistema (v5.0)

### 1️⃣ **Coleta de Dados (Bybit API)**
```
Bybit API → Market Data (30M + 4H)
```
- Sistema busca dados de **100 pares** (top volume) a cada intervalo
- Coleta métricas institucionais: **Open Interest**, **Long/Short Ratio**, **CVD**

#### 🌍 Localização Completa (PT-BR)
- Interface, logs, raciocínio dos agentes e relatórios: **100% em Português do Brasil**.

---

### 2️⃣ **Geração de Sinais & Inteligência Artificial**
```
Market Data → Signal Generator → AI Council Validation
```
**Estratégias:**
- **EMA Crossover**, **RSI + BB Reversal**, **Trend Pullback**, **Judas Swing** (Stop Hunts).

**Camada Neural (The Council):**
- **Scout**: Monitora reação de preço.
- **Sentinel**: Detecta fluxo oculto e absorção.
- **Governor**: Controla risco e correlação de portfólio.
- **Strategist**: Aprende com histórico (Post-Mortem).
- **Anchor**: Sincroniza com cenário Macro (DXY/SP500).

---

### 3️⃣ **Simulação de Banca (The Bankroll Manager) - NOVO**
```
Sinal Aprovado → Bankroll Manager → Simulação Realista ($20 -> $50k)
```
Uma camada de simulação financeira que opera como um "Trader de Elite" paralelo ao sistema de sinais:
- **Capital Inicial**: $20.00 (Simulação de conta pequena de alavancagem).
- **Gestão de Risco**: Risco fixo de **5% por trade**.
- **Alavancagem**: **50x** (High Risk/Reward).
- **Slots Ativos**: Máximo de **2 trades simultâneos** para evitar overtrading.
- **Objetivo**: Provar a viabilidade matemática do crescimento exponencial (Juros Compostos).

---

### 4️⃣ **Monitoramento Ativo (Smart Exits & Surf Logic)**
```
Trade Aberto → Monitor de Preço (5s) → Proteção e Alvos
```
- ✅ **Partial Take Profit**: Atingiu 2%? Stop Loss vai para o Breakeven (0x0).
- ✅ **Surf Logic**: Atingiu 3%? Trailing Stop liga e TP fixo é removido para capturar "Home Runs" (10-20%).
- ✅ **Sniper Target 6%**: Alvo base unificado para operações de alta precisão.
- ✅ **Flip Strategy (Reversão)**: Detectou armadilha (Trap)? O sistema inverte a mão automaticamente.

---

### 5️⃣ **Machine Learning Autônomo (Auto-Train)**
- **Treino Obrigatório**: O sistema valida o modelo a cada startup.
- **Retreino Dinâmico**: A cada 30 novos sinais finalizados, o modelo aprende os novos padrões.
- **Modo Fallback**: Se faltarem dados (<100 amostras), o sistema opera puramente por regras técnicas e Conselho de IA.

---

## 🛠️ Instalação e Uso (Core v5.0)

### Requisitos
- Python 3.10+
- Node.js 18+
- Supabase Account

### 1. Backend (Python/Flask)

```powershell
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Instalação Robusta de Dependências (v5.0 Fix)
pip install -r requirements.txt
```

**Iniciar o Servidor:**
```powershell
python app.py
```
*O backend iniciará em `http://localhost:5001` e fará a conexão assíncrona com o Supabase.*

### 2. Frontend (React/Vite)

```powershell
cd frontend
npm install
npm run dev
```
*Acesse o dashboard em `http://localhost:3001`.*

---

## 📝 Changelog

### v5.0 (Jan 2026 - The Bankroll Era - STABLE)
- ✅ **Bankroll Manager**: Motor de simulação financeira completo integrado ao fluxo de sinais.
- ✅ **System Stability Core**: Resolução definitiva de conflitos de dependência (`pytz`, `pandas`) e implementação de conexão de banco de dados assíncrona robusta.
- ✅ **Async Architecture**: Backend não bloqueia mais durante a inicialização ou falhas de rede do Supabase.
- ✅ **Full Translation**: Todo o ecossistema (Logs, UI, Agentes) traduzido para PT-BR.
- ✅ **Smart Money Hunger Index**: Refinamento na detecção de "fome" institucional por liquidez.

### v4.0 (Jan 2026 - Neural Intelligence)
- ✅ **Neural Agent Network**: 5 Agentes especializados (Scout, Sentinel, etc.).
- ✅ **Flip Strategy**: Reversão automática em armadilhas.
- ✅ **Agents Dashboard**: Visualização "divertida-mente" dos agentes.

### v3.x (Jan 2026 - Features)
- ✅ **Surf Logic & Live Sniper**: UI de progresso em tempo real.
- ✅ **Sentiment Analysis**: Integração com notícias e LLM.
- ✅ **Auto-Training**: ML autônomo.

---

## 🎯 Métricas Atuais (Jan/2026 - v5.0)

| Métrica | Valor |
|---------|-------|
| **Pares Monitorados** | 100 |
| **Banca Simulada (Inicial)** | $20.00 |
| **Risco por Trade** | 5% |
| **Win Rate (Histórico)** | ~33% (Alta assimetria de retorno) |
| **Status do ML** | Fallback (Coletando dados) / Ativo (>100 amostras) |

---

**⚠️ Disclaimer:** Este sistema é uma ferramenta de pesquisa e análise. O módulo "Bankroll" é uma simulação matemática. Trading real envolve risco de perda total.
