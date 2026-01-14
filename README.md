# 🚀 10D - Sistema de Sinais de Trading com IA

O **10D** é um scanner avançado de sinais para criptomoedas que monitora os top 100 pares da Bybit em tempo real (TF 30M), utilizando estratégias avançadas filtradas por tendência de tempo gráfico maior (4H) e **Machine Learning** para otimização contínua.

## ✨ Recursos

### 📈 Estratégias de Trading
-   **Institutional Judas Swing (30M):** Detecção de capturas de liquidez (stop hunts) em níveis de Suporte/Resistência, confirmadas por volume e reclaims rápidos.
-   **Order Flow Analysis:** Confirmações por Cumulative Volume Delta (CVD), Open Interest (OI) e Long/Short Ratio (LSR).
-   **Relative Strength (RS):** Comparação de performance entre altcoins e BTC para identificar força relativa institucional.
-   **EMA 20/50 + MACD:** Cruzamento de médias exponenciais filtrado por histograma.
-   **RSI + Bollinger Bands Reversal:** Detecção de reversões em extremos de RSI com confirmação de Bandas de Bollinger.
-   **Trend Pullback:** Entrada em pullbacks dentro de tendências fortes.
-   **4H Trend Filter:** Filtro global de tendência baseado no tempo gráfico de 4 horas.

### 🤖 Sistema de Machine Learning (M.E.)
-   **ML Training Bridge:** Serviço que coleta dados históricos do Supabase e gera insights para otimização.
-   **AI Features:** Captura automática de métricas de mercado (OI%, LSR%, CVD, RS, Volatilidade) em cada sinal.
-   **Brain JSON:** Arquivo de "cérebro" gerado com:
    -   Importância das features (correlação com Gain/Loss)
    -   Thresholds ótimos (Score mínimo, Range ideal de RSI)
-   **Feedback Loop:** Sinais finalizados (TP_HIT, SL_HIT, EXPIRED) são todos salvos no Supabase para treinamento contínuo.

### 📊 Monitoramento e Histórico
-   **Monitoramento Ativo em Tempo Real:** Acompanhamento contínuo de preços para todos os sinais gerados.
-   **Finalização Automática:** Detecção de Take Profit, Stop Loss e Expiração com salvamento no banco de dados.
-   **Cálculo de ROI Real:** ROI calculado automaticamente no momento da finalização.
-   **Histórico de Performance:** Dashboard dedicado para visualizar o desempenho de sinais anteriores.

### 🎨 Interface e Deploy
-   **Organizador de Trades (10M):** Planejador de 30 dias com juros compostos, metas diárias e persistência de dados.
-   **Interface Ultra-Premium:** Design moderno com Glassmorphism, ícones SVG customizados e feedbacks visuais dinâmicos.
-   **Mentor 10D:** Chat com IA (Gemini) para análise de trades e recomendações personalizadas.
-   **PWA & Mobile Ready:** Instalável como aplicativo no celular, com modo offline básico.
-   **Deployment Robusto:** Configurado para **Google Cloud Run** com **Gunicorn** e inicialização assíncrona.

## 🛠️ Tecnologias

-   **Backend:** Python 3.10+ (Flask, Gunicorn, Pandas, Requests)
-   **Frontend:** React (Vite, CSS Vanilla, Glassmorphism)
-   **Banco de Dados:** Supabase (PostgreSQL)
-   **IA/ML:** Google Gemini API, Pandas para análise de correlações
-   **Fuso Horário:** Ajustado para São Paulo (UTC-3)
-   **API de Dados:** Bybit V5 API

## 🚀 Como Começar

### Pré-requisitos
-   Python 3.10+
-   Node.js 18+
-   Conta no Supabase (para persistência)
-   Chave da API Gemini (para Mentor 10D)

### Passo 1: Configurar Variáveis de Ambiente
```bash
# backend/.env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_ANON_KEY=sua_chave_anonima
GEMINI_API_KEY=sua_chave_gemini
```

### Passo 2: Iniciar o Backend
```powershell
cd backend
# Instalar dependências
pip install -r requirements.txt
# Iniciar o servidor (Porta 5001)
python app.py
```

### Passo 3: Iniciar o Frontend
```powershell
cd frontend
# Instalar dependências
npm install
# Iniciar o servidor (Porta 3001)
npm run dev
```

### Passo 4: Acessar o Sistema
Abra o navegador em: **http://localhost:3001**

## 📊 Endpoints da API (Porta 5001)

### Sinais e Monitoramento
-   `GET /api/signals` - Retorna sinais ativos com score
-   `GET /api/stats` - Resumo de pares monitorados e estatísticas
-   `GET /api/history` - Histórico dos sinais finalizados
-   `GET /api/pairs` - Lista dos 100 pares sendo escaneados

### Machine Learning e Analytics
-   `GET /api/ai/analytics` - Correlações e insights da IA
-   `GET /api/ai/progress` - Progresso da coleta de dados para treinamento

### Mentor IA
-   `POST /api/mentor/chat` - Chat com o Mentor 10D (Gemini)

### Plano de Trading
-   `GET/PUT /api/users/artifacts/trading-plan` - Salva e recupera o plano de trades (10M)

## 🧠 Arquitetura do ML

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Signal         │────▶│   Supabase       │────▶│  ML Training    │
│  Generator      │     │   (signals DB)   │     │  Bridge         │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
        │                                                  │
        │                                                  ▼
        │                                        ┌─────────────────┐
        │◀───────────────────────────────────────│  ml_brain.json  │
        │         (optimal thresholds)           │  (insights)     │
        │                                        └─────────────────┘
```

### Serviços Principais

| Arquivo | Função |
|---------|--------|
| `signal_generator.py` | Gera e monitora sinais, captura ai_features |
| `database_manager.py` | CRUD no Supabase, contagem de sinais para ML |
| `ai_analytics_service.py` | Análise de correlações e preparação de dados |
| `ml_training_bridge.py` | Executa ciclo de "treinamento" e gera insights |
| `ai_assistant_service.py` | Mentor 10D (chat com Gemini) |

## 📈 Métricas Atuais (Jan/2026)

| Métrica | Valor |
|---------|-------|
| Sinais Analisados | 73 |
| Win Rate (TP/SL) | 70.8% |
| Features Mais Importantes | LSR%, RSI, CVD |
| Score Mínimo Sugerido | 84.12 |
| RSI Ideal | 45.3 - 63.9 |

## 🎯 Configurações da Estratégia

As definições de média móvel, RSI, TP/SL e filtragem estão localizadas em `backend/config.py`.

Principais configurações:
-   `STOP_LOSS_PERCENT`: 1% (padrão)
-   `TAKE_PROFIT_PERCENT`: 2% (padrão)
-   `SIGNAL_TTL_MINUTES`: 120 (expiração em 2 horas)
-   `PAIR_LIMIT`: 100 (número de pares monitorados)

---
**Disclaimer:** Este sistema é uma ferramenta de auxílio à análise e não garante lucros. Sempre gerencie seu risco com Stop Loss.
