# 🚀 10D - Sistema de Sinais de Trading com IA

Sistema avançado de análise e geração de sinais para criptomoedas que monitora os **top 100 pares da Bybit** em tempo real, utilizando estratégias técnicas filtradas por tendência e **Machine Learning** para otimização contínua.

---

## 📊 Diagrama do Sistema

![System Flow Diagram](C:/Users/spcom/.gemini/antigravity/brain/33428682-b703-452a-81e2-7793345a2290/system_flow_diagram_1768441484224.png)

---

## 🔄 Fluxo Completo do Sistema

### 1️⃣ **Coleta de Dados (Bybit API)**
```
Bybit API → Market Data (30M + 4H)
```
- Sistema busca dados de **100 pares** (top volume) a cada intervalo
- Coleta candles de **30 minutos** (timeframe principal)
- Coleta candles de **4 horas** (filtro de tendência)
- Coleta métricas de derivativos: **Open Interest**, **Long/Short Ratio**, **CVD**

### 2️⃣ **Geração de Sinais (Signal Generator)**
```
Market Data → Signal Generator → Aplica 4 Estratégias
```
**Estratégias:**
- **EMA Crossover** (20/50) + MACD
- **RSI + Bollinger Bands Reversal**
- **Trend Pullback** (entrada em correções)
- **Judas Swing** (stop hunts institucionais)

**Filtros aplicados:**
- ✅ Tendência 4H alinhada
- ✅ Volume acima da média
- ✅ Confirmação de Order Flow (CVD, OI, LSR)

### 3️⃣ **Cálculo de Score (Signal Scorer)**
```
Sinal Gerado → Signal Scorer → Score 0-100
```
Cada sinal recebe um **score de 0 a 100** baseado em:
- **Força da tendência** (30 pontos)
- **Confluência de indicadores** (25 pontos)
- **Order Flow positivo** (25 pontos)
- **Relative Strength vs BTC** (20 pontos)

**⚠️ Apenas sinais com score = 100 são salvos!**

### 4️⃣ **Salvamento no Banco (Database Manager)**
```
Score >= 100 → Salva no Supabase
```
Sinal é salvo com todas as informações:
```json
{
  "id": "BTCUSDT_1736897276988",
  "symbol": "BTCUSDT",
  "direction": "LONG",
  "entry_price": 45000,
  "stop_loss": 44550,
  "take_profit": 45900,
  "score": 100,
  "status": "ACTIVE",
  "ai_features": {
    "rsi_value": 58.3,
    "oi_change_pct": 2.5,
    "lsr_value": 1.8,
    "cvd_delta": 15000,
    "rs_score": 0.85,
    "master_score": 100
  }
}
```

### 5️⃣ **Monitoramento Ativo (Background Scanner)**
```
Sinal Ativo → Monitor de Preço → Verifica TP/SL/Expiração
```
- Sistema monitora **preço em tempo real** de todos os sinais ativos
- Verifica se atingiu **Take Profit** (2% de lucro)
- Verifica se atingiu **Stop Loss** (1% de perda)
- Verifica se **expirou** (2 horas sem atingir TP/SL)

### 6️⃣ **Finalização do Sinal**
```
TP/SL/Expirado → Atualiza Status → Salva no Histórico
```
Quando TP, SL ou expiração acontece:
```python
signal["status"] = "TP_HIT"  # ou "SL_HIT" ou "EXPIRED"
signal["final_roi"] = 2.0  # ROI real calculado
signal["exit_timestamp"] = 1736900000000
```

### 7️⃣ **Análise de IA (AI Analytics Service)**
```
Sinais Finalizados → AI Analytics → Calcula Métricas
```
Com sinais finalizados, o sistema calcula:
- **Win Rate**: % de sinais que atingiram TP
- **Performance por Estratégia**: Qual estratégia tem melhor taxa de acerto
- **Correlação de Features**: Quais métricas (RSI, OI, LSR) mais correlacionam com ganhos
- **Score Médio**: Comparação entre sinais vencedores vs perdedores

### 8️⃣ **Treinamento ML (ML Training Bridge)**
```
300+ Sinais → ML Training Bridge → Gera ml_brain.json
```
Quando há **300+ sinais finalizados**:
- Analisa todas as `ai_features` vs resultado (TP_HIT/SL_HIT)
- Identifica **thresholds ótimos** (ex: RSI ideal entre 45-64)
- Calcula **importância de features** (ex: LSR tem 35% de importância)
- Gera arquivo **`ml_brain.json`** com insights

### 9️⃣ **Otimização Contínua (Feedback Loop)**
```
ml_brain.json → Signal Scorer → Ajusta Thresholds
```
O `ml_brain.json` é usado para:
- Ajustar **score mínimo** (ex: só aceitar score >= 85)
- Aplicar **penalidades** (ex: RSI fora do range ideal perde 10 pontos)
- Aplicar **bônus** (ex: RSI no range ideal ganha 5 pontos)

### 🔟 **Exibição no Frontend (React PWA)**
```
Supabase → REST API → Frontend → Usuário
```
Usuário acessa 4 páginas principais:

**📊 Dashboard:**
- Sinais ativos com score 100
- Preço atual vs Entry/TP/SL
- Tempo restante até expiração

**📜 Histórico:**
- Sinais finalizados (últimas 24h)
- ROI real de cada trade
- Filtros por status (TP/SL/Expirado)

**🧠 Auditoria de IA:**
- Win Rate geral
- Performance por estratégia
- Insights do ML Brain
- Progresso da coleta de dados (X/300)

**💬 Mentor 10D:**
- Chat com IA (Gemini)
- Análise de trades
- Recomendações personalizadas

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|--------|------------|
| **Backend** | Python 3.10, Flask, Gunicorn |
| **Frontend** | React, Vite, CSS Vanilla |
| **Banco de Dados** | Supabase (PostgreSQL) |
| **IA/ML** | Google Gemini API, Pandas |
| **API de Dados** | Bybit V5 API |
| **Deploy** | Google Cloud Run |

---

## 🚀 Como Rodar Localmente

### 1. Configurar Variáveis de Ambiente

Crie `backend/.env`:
```bash
SUPABASE_URL=https://abphpbylwlgozmyumiwx.supabase.co
SUPABASE_ANON_KEY=sua_chave_anonima
GEMINI_API_KEY=sua_chave_gemini
```

### 2. Iniciar Backend

```powershell
cd backend
pip install -r requirements.txt
python app.py
```
Backend roda em: **http://localhost:5001**

### 3. Iniciar Frontend

```powershell
cd frontend
npm install
npm run dev
```
Frontend roda em: **http://localhost:3001**

---

## 📡 Endpoints da API

### Sinais
- `GET /api/signals` - Sinais ativos (score 100)
- `GET /api/history` - Histórico (últimas 24h)
- `GET /api/stats` - Estatísticas gerais
- `POST /api/scan` - Forçar scan manual

### AI Analytics
- `GET /api/ai/analytics` - Correlações e performance
- `GET /api/ai/progress` - Progresso da coleta (X/300)
- `GET /api/ai/brain` - Insights do ML Brain

### Debug
- `GET /api/version` - Versão do build
- `GET /api/debug/supabase` - Status da conexão com DB

---

## 📈 Arquitetura de Arquivos

```
10D-2.0/
├── backend/
│   ├── app.py                      # API Flask principal
│   ├── config.py                   # Configurações (TP/SL, timeframes)
│   ├── requirements.txt            # Dependências Python
│   └── services/
│       ├── signal_generator.py     # Gera e monitora sinais
│       ├── signal_scorer.py        # Calcula score (0-100)
│       ├── database_manager.py     # CRUD Supabase
│       ├── ai_analytics_service.py # Análise de performance
│       ├── ml_training_bridge.py   # Treinamento ML
│       └── ai_assistant_service.py # Mentor 10D (Gemini)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Roteamento principal
│   │   └── components/
│   │       ├── Dashboard.jsx       # Sinais ativos
│   │       ├── HistoryView.jsx     # Histórico
│   │       ├── AIAnalytics.jsx     # Auditoria de IA
│   │       └── MentorChat.jsx      # Chat com IA
│   └── package.json
└── README.md
```

---

## 🎯 Métricas Atuais (Jan/2026)

| Métrica | Valor |
|---------|-------|
| **Pares Monitorados** | 100 |
| **Sinais no Banco** | 200 |
| **Sinais Finalizados** | 76 (TP: 25, SL: 51) |
| **Win Rate** | 33% (25/76) |
| **Sinais com AI Features** | 200 (100%) |
| **Pronto para ML** | ✅ 76 amostras |

---

## 🔧 Configurações Principais

Edite `backend/config.py`:

```python
STOP_LOSS_PERCENT = 1.0      # 1% de stop
TAKE_PROFIT_PERCENT = 2.0    # 2% de lucro
SIGNAL_TTL_MINUTES = 120     # 2 horas de validade
PAIR_LIMIT = 100             # Top 100 pares
UPDATE_INTERVAL_SECONDS = 60 # Scan a cada 1 minuto
```

---

## 🐛 Troubleshooting

### Problema: Auditoria de IA sem dados
**Solução:** Verifique se `supabase==2.9.0` está instalado (versões antigas causam erro de `proxy`)

### Problema: Backend não conecta ao Supabase
**Solução:** Verifique variáveis de ambiente no Cloud Run ou `.env` local

### Problema: Frontend não carrega sinais
**Solução:** Confirme que backend está rodando em `localhost:5001`

---

## 📝 Changelog

### v2.0 (Jan 2026)
- ✅ Fix: Atualizado `supabase==2.9.0` para resolver TypeError
- ✅ Feature: Endpoint `/api/debug/supabase` para diagnóstico
- ✅ Feature: Logs aprimorados em `database_manager.py`
- ✅ Feature: Build version tracking em produção

### v1.0 (Dez 2025)
- Lançamento inicial com 4 estratégias
- Integração com Supabase
- ML Training Bridge
- Interface PWA

---

**⚠️ Disclaimer:** Este sistema é uma ferramenta de auxílio à análise técnica. Não garante lucros. Sempre opere com Stop Loss e gestão de risco adequada.

**📧 Suporte:** Para dúvidas ou problemas, consulte os logs do Cloud Run ou teste localmente primeiro.
