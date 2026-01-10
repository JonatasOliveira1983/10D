# 🚀 10D - Sistema de Sinais de Trading

O **10D** é um scanner avançado de sinais para criptomoedas que monitora os top 100 pares da Bybit em tempo real (TF 30M), utilizando estratégias avançadas filtradas por tendência de tempo gráfico maior (4H).

## ✨ Recursos

-   **Estratégias Avançadas:** 
    -   **EMA 20/50 + MACD:** Cruzamento de médias exponenciais confirmado pelo histograma MACD.
    -   **4H Trend Filter:** Filtro global baseado na EMA 50 do gráfico de 4 horas para maior assertividade.
    -   **RSI + Bollinger Reversão:** Identificação de exaustão em bandas extremas.
    -   **Pullback na Tendência:** Entradas precisas em retrações para a EMA 20.
-   **Scoring Dinâmico:** Avalia a força do sinal de 0 a 100 com emojis e ratings humanizados.
-   **Multi-Pair:** Monitora os 100 maiores pares por volume (BTCUSDT excluído para focar em altcoins).
-   **Totalmente Responsivo:** Interface otimizada para Desktop e Mobile (com Bottom Nav e Sidebar).
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

## 🎯 Configurações da Estratégia
As definições de média móvel, RSI e filtragem estão localizadas em `backend/config.py`.

---
**Disclaimer:** Este sistema é uma ferramenta de auxílio à análise e não garante lucros. Sempre gerencie seu risco com Stop Loss.
