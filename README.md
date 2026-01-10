# 🚀 10D - Sistema de Sinais de Trading

O **10D** é um scanner avançado de sinais para criptomoedas que monitora os top 100 pares da Bybit em tempo real (TF 30M), utilizando estratégias avançadas filtradas por tendência de tempo gráfico maior (4H).

## ✨ Recursos

-   **Estratégias Avançadas:** 
    -   **EMA 20/50 + MACD:** Cruzamento de médias exponenciais confirmado pelo histograma MACD.
    -   **4H Trend Filter:** Filtro global baseado na EMA 50 do gráfico de 4 horas.
    -   **RSI + Bollinger Reversão:** Identificação de exaustão em bandas extremas.
    -   **Pullback na Tendência:** Entradas precisas em retrações para a EMA 20.
-   **Organizador de Trades (10M):** Planejador de 30 dias com juros compostos, metas diárias e persistência de dados no servidor (`trading_plan.json`).
-   **PWA & Mobile Ready:** Instalável como aplicativo no celular, com modo offline básico e ícones premium.
-   **Interface Premium:** Design ultra-moderno com Glassmorphism, ícones SVG customizados (azul envidraçado) e transições suaves.
-   **Página de Abertura:** Splash screen motivacional com animações e frases inspiradoras.
-   **Deployment Robusto:** Configurado para **Google Cloud Run** com **Gunicorn** e inicialização assíncrona.

## 🛠️ Tecnologias

-   **Backend:** Python 3.10+ (Flask, Gunicorn, Pandas, Requests).
-   **Frontend:** React (Vite, CSS Vanilla, Glassmorphism).
-   **Fuso Horário:** Ajustado para São Paulo (UTC-3).
-   **API:** Bybit V5 API.

## 🚀 Como Começar

### Pré-requisitos
-   Python 3.10+
-   Node.js 18+

### Passo 1: Iniciar o Backend
```powershell
cd backend
# Instalar dependências
pip install -r requirements.txt
# Iniciar o servidor (Porta 5001)
$env:PYTHONIOENCODING="utf-8"; python app.py
```

### Passo 2: Iniciar o Frontend
```powershell
cd frontend
# Instalar dependências
npm install
# Iniciar o servidor (Porta 3000)
npm run dev
```

## 📊 Endpoints da API (Porta 5001)

-   `GET /api/signals`: Retorna sinais ativos com score.
-   `GET /api/stats`: Resumo de pares monitorados e estatísticas de sinais.
-   `GET /api/history`: Histórico dos sinais gerados.
-   `GET /api/pairs`: Lista dos 100 pares sendo escaneados.
-   `GET/PUT /api/users/artifacts/trading-plan`: Salva e recupera o plano de trades (10M).

## 🎯 Configurações da Estratégia
As definições de média móvel, RSI e filtragem estão localizadas em `backend/config.py`.

---
**Disclaimer:** Este sistema é uma ferramenta de auxílio à análise e não garante lucros. Sempre gerencie seu risco com Stop Loss.
