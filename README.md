# 🚀 10D - Sistema de Sinais de Trading com IA (v4.0)

Sistema avançado de análise e geração de sinais para criptomoedas que monitora os **top 100 pares da Bybit** em tempo real, utilizando estratégias técnicas filtradas por tendência e **Machine Learning Autônomo** para otimização contínua.

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

#### 🌍 Localização e Idioma
- **Interface Completa em Português (PT-BR):** Todos os agentes, métricas e insights são apresentados em português nativo.
- **Raciocínio Adaptado:** Os agentes (Strategist, Governor, Anchor) foram instruídos a gerar pensamentos e relatórios diretamente em PT-BR.

## 🛠️ Instalação e Uso

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

### 5️⃣ **Monitoramento Ativo (Background Scanner & Smart Exits)**
```
Sinal Ativo → Monitor de Preço → Aplica Saídas Inteligentes → TP/SL
```
- **Monitoramento em Tempo Real**: Verifica preço a cada 5 segundos.
- ✅ **Partial Take Profit**: Ao atingir **2% de lucro**, o sistema move o Stop Loss para o **Preço de Entrada (Breakeven)**. Lucro protegido!
- ✅ **Trailing Stop**: Ao atingir **3% de lucro**, o Trailing Stop é ativado. O SL segue o preço a uma distância de 1%.
- ✅ **Surf Logic (NOVO)**: Ao ativar o Trailing Stop (em 3%), o sistema ignora o Take Profit fixo e deixa a operação correr para capturar movimentos de **10% a 15%+**.
- ✅ **Sniper Target 6%**: Todos os sinais Sniper agora buscam um alvo inicial unificado de **6%**, com proteção de capital garantida.
- **Expiração**: 2 horas de validade caso o preço não atinja os alvos.
- ✅ **Reversão de Posição (FLIP)**: Se o Scout e o Sentinel detectarem uma **Bull/Bear Trap**, o sistema executa um "Stop & Reverse", fechando a posição atual e abrindo uma na direção oposta para capturar o rompimento real.

### 6️⃣ **Finalização do Sinal & Relatórios**
```
TP/SL/Expirado → Gera Relatório de Decisão → Salva no Histórico
```
Quando TP, SL ou expiração acontece:
- **Relatório de Decisão (NOVO)**: O sistema gera uma narrativa detalhada do trade, guardando o estado dos indicadores (RSI, CVD, OI), o veredito do Conselho de IA e o sentimento do mercado naquele momento.
- **Histórico Rico**: Esses relatórios são visualizados expandindo os cartões no histórico.

### 7️⃣ **Aprendizado Contínuo (RAG & Feedback Loop)**
- **RAG Memory**: Todo sinal finalizado alimenta a memória de longo prazo (RAG).
- **Loop de Feedback**: Antes de validar um novo sinal, o Conselho de IA consulta os "trades similares" do passado para evitar repetir erros ou replicar sucessos.
- **Auto-Retrain ML**: Treinamento matemático autônomo continua ocorrendo a cada 30 amostras.

### 7️⃣ **Análise de IA (AI Analytics Service)**
```
Sinais Finalizados → AI Analytics → Calcula Métricas
```
Com sinais finalizados, o sistema calcula:
- **Win Rate**: % de sinais que atingiram TP
- **Performance por Estratégia**: Qual estratégia tem melhor taxa de acerto
- **Correlação de Features**: Quais métricas (RSI, OI, LSR) mais correlacionam com ganhos
- **Score Médio**: Comparação entre sinais vencedores vs perdedores

### 8️⃣ **Treinamento ML Autônomo (Continuous Training)**
```
Sinais Finalizados → ML Predictor → Auto-Training
```
- **Treinamento no Startup**: O sistema treina o modelo obrigatoriamente ao iniciar o backend.
- **Auto-Retrain**: Retreina automaticamente a cada **30 novas amostras** finalizadas.
- **Threshold de Accuracy**: Se a acurácia cair abaixo de **55%**, um retreino emergencial é disparado.
- **Feedback Real-time**: O progresso é visível no frontend com barras de progresso dinâmicas.

### 9️⃣ **Filtragem por Probabilidade (Acurácia de IA)**
```
Sinal Gerado → Predict Probability → Threshold 40%
```
O modelo ML analisa 15+ features para cada sinal e só aprova se:
- ✅ Probabilidade de sucesso >= **40%** (Configurável)
- ✅ Acurácia do modelo validada no último treino
- ✅ Alinhamento com os melhores thresholds de RSI/OI/LSR históricos

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

**🎯 Live Sniper Monitor (NOVO):**
- Monitoramento visual de todos os sinais ativos em tempo real.
- Barra de progresso dinâmica de 0% a 6%+.
- Badges indicadores: "TP Parcial ✅" e "Trailing Stop 🔥".
- Monitoramento de **Highest ROI** atingido durante o trade.

**🧠 Auditoria de IA:**
- Win Rate geral e métricas do modelo (Precision, Recall, F1)
- ✨ **Auto-Training Status**: Barra de progresso para o próximo retreino
- Insights de importância de features (quais indicadores mais pesam)
- Histórico de acurácia das últimas versões do modelo

**💬 Mentor 10D:**
- Chat com IA (Gemini)
- Análise de trades
- Recomendações personalizadas

---

## 🚦 Fluxo de Vida do Sinal (The Lifecycle)

Desmistificando como o 10D opera do início ao fim:

### 1. Nascimento & Filtros (O Funil)
Nem todo sinal vira trade. O funil é rigoroso:
- **Filtro Técnico**: Scan em 100 pares. Se o Score < 100, é descartado.
- **Filtro de Regime (Novo)**: Se BTC está Lateral, apenas moedas "Desgrudadas" passam.
- **Filtro de IA**: O modelo ML calcula a probabilidade. Se < 50%, é bloqueado.

### 2. Monitoramento Inteligente (A Onda)
Uma vez aprovado, o sinal entra no **Live Monitor** (loop de 5 segundos):
- **Alvo Dinâmico**: O sistema persegue 2% de lucro inicial.
- **Proteção Rápida**: Bateu 2%? O **Stop Loss sobe para a Entrada** (Risco Zero).
- **Surf Logic**: Bateu 3%? O **Trailing Stop** liga. O TP fixo é ignorado e o sistema deixa o lucro correr até a tendência virar.

### 3. Finalização & Aprendizado (O Ciclo)
O sinal morre quando bate no Stop (Normal ou Trailing) ou expira.
- **Auto-Training**: A cada 30 sinais finalizados, o sistema **automaticamente** re-treina o cérebro da IA.
- **Quem controla o treino?** É um algoritmo determinístico (Python), não a LLM. A LLM **consome** os dados gerados para dar conselhos, mas o treino matemático é feito pelo Scikit-Learn.

---

## 🧠 Rede Neural de Agentes (Neural Agent Network)

O 10D evoluiu para uma rede neural de agentes especializados que colaboram para maximizar a precisão:

| Agente | Missão | Momento de Atuação |
|--------|---------|-------------------|
| **Scout (Batedor)** | Monitora a reação do preço e a força do viés. | Durante o Trade |
| **Sentinel (Sentinela)** | Detecta absorção e manipulação institucional (Order Flow). | Durante o Trade |
| **Strategist (Estrategista)** | Aprende com o histórico e faz o "Post-Mortem" das perdas. | Pós-Trade / Contínuo |
| **Portfolio Governor** | Controla a correlação e impede exposição excessiva. | Pré-Trade |
| **Global Anchor** | Sincroniza o sistema com o cenário Macro (DXY/SP500). | Global / Contínuo |
| **Health Monitor** | Garante a integridade técnica (CPU/DB/API). | Infraestrutura |

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
Frontend roda em: **http://localhost:3001** (Conforme configurado em `vite.config.js`)

---

## 📡 Endpoints da API

### Sinais
- `GET /api/signals` - Sinais ativos (score 100)
- `GET /api/history` - Histórico (últimas 24h)
- `GET /api/stats` - Estatísticas gerais
- `POST /api/scan` - Forçar scan manual

### Sistema & Agentes
- `GET /api/system/health` - Vitals do sistema e diagnóstico de IA
- `GET /api/system/agents` - Status, missões e reflexões de todos os agentes (Dashboard Agentes)

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
│       ├── ai_assistant_service.py # Mentor 10D (Gemini)
│       └── llm_agents/             # 🧠 Camada de Agentes Especializados
│           ├── adaptive_bias_agent.py    # O Scout (Preço)
│           ├── liquidity_sentinel_agent.py # O Sentinel (Fluxo)
│           ├── strategist_agent.py       # O Estrategista (Learning)
│           ├── portfolio_governor_agent.py # O Governor (Risco)
│           └── global_anchor_agent.py    # O Anchor (Macro)
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
SIGNAL_TTL_MINUTES = 120     # 2 horas de validade (expiração)
PAIR_LIMIT = 100             # Monitora os top 100 pares
ML_ENABLED = True            # Ativa/Desativa o motor de ML
ML_PROBABILITY_THRESHOLD = 0.50 # 50% de confiança mínima da IA (Atualizado)
ML_MIN_SAMPLES = 100         # Sinais necessários para 1º treino
ML_AUTO_RETRAIN_INTERVAL = 30 # Retreina a cada 30 novas amostras
```

---

## Estratégia Sniper (BTC Regime)

O sistema utiliza uma lógica avançada baseada no regime do Bitcoin para maximizar os lucros (Alvo de 6%+) e reduzir ruídos:

- **BTC Lateral (Ranging)**: O sistema entra em modo Sniper **APENAS** para moedas "desgrudadas" (Decoupling Score > 0.45). Sinais correlacionados são **REJEITADOS**. Alvo: 6%.
- **BTC em Tendência (Trending)**: Apenas sinais "Elite" com Score técnico de 100% e Probabilidade ML > 50% são aceitos. Alvo: 6%.
- **Monitoramento Exclusivo**: Sinais que não atendem aos critérios Sniper são automaticamente descartados da memória e do banco de dados para focar apenas nas operações de alto ganho.

## 🐛 Troubleshooting

### Problema: Auditoria de IA sem dados
**Solução:** Verifique se `supabase==2.9.0` está instalado (versões antigas causam erro de `proxy`)

### Problema: Backend não conecta ao Supabase
**Solução:** Verifique variáveis de ambiente no Cloud Run ou `.env` local

### Problema: Frontend não carrega sinais
**Solução:** Confirme que o backend está rodando em `localhost:5001`.

### Problema: Erro 404 ao acessar localhost:3001 (Página não encontrada)
**Solução:** 
1. Verifique se o processo do Vite não travou em outra porta (ex: 3000).
2. Verifique o arquivo `frontend/vite.config.js` e garanta que `server.port` está definido como `3001`.
3. Tente matar processos antigos do Node: `taskkill /F /IM node.exe /T` (Windows).
4. Limpe o cache do navegador (F5).


---

## 📝 Changelog

### v4.0 (Jan 2026 - Neural Intelligence Phase)
- ✅ **Neural Agent Network**: Implementação de 5 agentes especializados para gestão dinâmica (Scout, Sentinel, Strategist, Governor, Anchor).
- ✅ **Flip Strategy (Stop & Reverse)**: Sistema agora detecta armadilhas institucionais (Traps) e inverte a posição para capturar o rompimento real.
- ✅ **Agentes Dashboard**: Nova página no frontend para monitorar a saúde e o "pensamento" de cada agente em tempo real.
- ✅ **Portfolio Governance**: Proteção contra correlação excessiva e gestão de exposição global.
- ✅ **Global Anchor**: Integração de dados Macro (DXY, SP500) para ajuste dinâmico de confiança.

### v3.9 (Jan 2026 - Experience Refinement)
- ✅ **Decision Reports**: Narrativas geradas automaticamente ao fechar sinais, consolidando o "porquê" de cada trade.
- ✅ **Signal Journey Persistence**: Sinais finalizados ficam 5min extras no monitor ativo com status celebratório.
- ✅ **Super Profit Visuals**: Novo visual neon/glow para trades que superam o alvo (ex: AXS).
- ✅ **RAG Feedback Loop**: Integração profunda entre os resultados do histórico e a validação de novos sinais (RAG Learning).
- ✅ **UI Stability**: Correção de vazamento de barras de progresso em ROIs explosivos.

### v3.8 (Jan 2026 - Ranging Enforcer)
- ✅ **Strict Ranging Filter**: No regime BTC Ranging, apenas sinais com Decoupling Score > 0.45 são aceitos.
- ✅ **ML Threshold Update**: Probabilidade mínima da IA aumentada para 50% (era 40%) para maior qualidade.

### v3.9 (Jan 2026 - Smart Money Hunger Index)
- ✅ **IHI (Institutional Hunger Index)**: Detecção granular (1-6) de atividade institucional baseada em OI, LSR e CVD.
- ✅ **LED Dots UI**: Sistema visual discreto de 6 pontos para indicar o nível de "fome" de caça à liquidez.
- ✅ **Council Integration**: O Conselho de IA agora pondera a Fome Institucional em cada decisão de sinal.
- ✅ **Extreme High Intensity Pulse**: Animação pulsante vermelha para IHI >= 5 (Squeeze e liquidações iminentes).

### v3.8 (Jan 2026 - Signal Journey Polish)
- ✅ **Finalized Persistence**: Sinais finalizados agora permanecem 5 minutos na lista ativa para visualização do resultado.
- ✅ **Super-Profit Neon**: Visual com degradê neon animado e efeito "bounce" para trades que superam o Take Profit.
- ✅ **Progress Bar Overflow Fix**: Correção de design que impedia barras de ROI alto de vazar do card.
- ✅ **Celebratory Badges**: Novos badges de "ALVO ATINGIDO" e "STOP LOSS" com efeitos de brilho (Success Glow).

### v3.7 (Jan 2026 - Surf Logic & Profit Max)
- ✅ **Surf Logic**: Se o Trailing Stop estiver ativo, o TP fixo é ignorado para capturar 10%+ de lucro.
- ✅ **Fast Breakeven**: SL movido para entrada automaticamente ao atingir 2% de ROI.
- ✅ **Unified Sniper Target**: Alvo de 6% padrão para todos os sinais Sniper qualificados.
- ✅ **Price Update Batch Fix**: Corrigido erro de sincronização de preços em lote para sinais ativos.

### v3.6 (Jan 2026 - Stability & Windows Fixes)
- ✅ **Council Stability**: Melhoria na detecção de "Rate Limit" do Gemini, evitando erros de processamento genéricos.
- ✅ **Non-blocking Council**: O sistema não trava mais se a IA atingir limites de taxa; ele segue com fallback seguro.
- ✅ **Windows Encoding Fix**: Remoção completa de caracteres não-ASCII e emojis de logs críticos para evitar crashes em terminais Windows.
- ✅ **Improved Error Handling**: Lógica de erro do CouncilManager refinada para diferenciar falhas técnicas de rejeições de sinais.

### v3.5 (Jan 2026 - Sentiment Intelligence)
- ✅ **Sentiment Analysis**: Novo motor que analisa o "humor do mercado" em tempo real.
- ✅ **News Integration**: Coleta automática de manchetes (CoinTelegraph/CoinDesk).
- ✅ **LLM Upgrade**: A IA agora considera o sentimento (Fear/Greed) para validar sinais.
- ✅ **Frontend Widget**: Novo painel de Sentimento no Signal Journey.

### v3.4 (Jan 2026 - Signal Journey & Self-Learning)
- ✅ **Signal Journey Dashboard**: Visualização unificada de Sinais + Histórico + Analytics em uma única tela.
- ✅ **Internationalization (i18n)**: Suporte completo a PT-BR, English e Español.
- ✅ **LLM Self-Learning**: O sistema agora aprende com o histórico do Supabase (1.104+ sinais) para tomar decisões melhores.
- ✅ **Settings Page**: Página de configurações para troca de idioma e tema.
- ✅ **PWA Cache Fix**: Build otimizado para expiração de cache.

### v3.3 (Jan 2026 - Live Sniper Refined)
- ✅ **Current ROI Tracking**: ROI atual exibido em tempo real em cada card.
- ✅ **Real-time Trailing Stop Persistence**: Atualizações do trailing stop são salvas imediatamente no banco.
- ✅ **Pin to Top**: Novo botão para fixar sinais no topo (persiste no localStorage).
- ✅ **Responsive Design**: Layout adaptativo para mobile e tablets.
- ✅ **UI Improvements**: Dual ROI display (Atual + Máximo), labels corrigidos na barra de progresso.
- 🐛 **Bug Fix**: Variável `hit` não inicializada corrigida.
- 🐛 **Bug Fix**: Função `round_step` movida para nível de módulo.

### v3.2 (Jan 2026 - Smart Exits & Live Sniper)
- ✅ **Partial Take Profit**: Proteção automática no 0x0 ao atingir 2% de lucro.
- ✅ **Trailing Stop**: Lucro móvel ativado nos 3% para buscar alvos de 6%+.
- ✅ **Live Sniper Interface**: Nova página de monitoramento real-time com barras de progresso.
- ✅ **Database Persistence**: Novo suporte para rastreamento de ROI máximo atingido.

### v3.1 (Jan 2026 - Turbo Logic Update)
- ✅ **BTC Regime Tracker**: Sistema detecta Ranging/Trending/Breakout automaticamente.
- ✅ **Decoupling Score**: Identifica moedas agindo independentes do BTC.
- ✅ **Turbo Strategy**: Aplica alvos de Breakout (TP ~3%) para moedas desacopladas, ignorando regime lateral.
- ✅ **Enhanced Vision**: Badges visuais no Frontend para Regime e Decoupling status.

### v3.0 (Jan 2026 - ML Evolution)
- ✅ **Auto-Training**: Sistema retreina sozinho a cada 30 amostras.
- ✅ **Startup Training**: Backend treina ML obrigatoriamente ao iniciar.
- ✅ **UI Sync**: Nova barra de progresso e status de treino em tempo real.
- ✅ **Optimized Threshold**: ML Threshold baixado para 40% para maior volume.
- ✅ **Robustness**: Implementado modo Fallback (sistema não trava sem modelo).

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
