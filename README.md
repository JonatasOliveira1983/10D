# 10D Trading System v5.1 (Eagle Elite)

**10D** is an advanced automated trading system powered by AI/ML and Large Language Models (LLM) to identify high-probability crypto setups.

## 🚀 Status: OPERATIONAL
- **Frontend**: "Neural Interface" Dashboard (React + Tailwind) - **PORT 3001**
- **Backend**: Flask API + Python + Supabase - **PORT 5001**
- **AI Core**: Active (Scout, Sentinel, Strategist Agents)

## 🖥️ Neural Interface (Premium)
O sistema foi consolidado para usar exclusivamente a interface **Premium**:
- **Sala de Situação Tática**: Localizada na aba **Banca**, permite monitoramento profissional.
- **Gráficos Multi-Timeframe**: Suporte a 1M, 5M, 15M, 30M, 1H, 2H, 4H e 1D.
- **Elite Bankroll Captain V2**: IA dedicada com gestão persistente (Supabase):
    - **Ciclo de 20 Trades**: Gestão de juros compostos por estágios (lote fixo por ciclo).
    - **Memória de Aprendizado**: Tabela `agent_learning` para persistência de lições táticas.
    - **Performance Sniper**: Alvos dinâmicos de até 6% (300% ROI com alavancagem 50x).
- **PWA Push Notifications**: Alertas em tempo real no celular mesmo com o App fechado.
    - Notificações de Gain/Loss.
    - Resumos de conclusão de Ciclo.
    - Gatilho "Real Money Ready" (70% Win Rate).
- **Agent HUD**: Telemetria em tempo real sobre o gráfico com o "pensamento" da IA.
- **Dark Glassmorphism**: Estética premium com fundos escuros e acentos neon.
- **Responsividade Ótima**: Ajustado para Desktop e Mobile.

## 🛠️ Execução do Sistema

### 1. Backend (Python/Flask)
```bash
# O Backend DEVE rodar na porta 5001
python backend/app.py
```
*Configurado via `backend/config.py` (`API_PORT = 5001`).*

### 2. Frontend (React/Vite)
```bash
cd frontend
# O Frontend DEVE rodar na porta 3001
npm run dev
```
*Configurado via `vite.config.js` (`port: 3001`).*

> [!IMPORTANT]
> **Padrão de Portas:**
> - Frontend: http://localhost:3001
> - Backend: http://localhost:5001
> 
> Qualquer outra porta (3002, 3003, 5000) é residual e deve ser ignorada ou o processo deve ser encerrado.

## ⚠️ Troubleshooting (Problemas Comuns)

### "Interface Antiga ou Incompleta aparecendo"
Se ao acessar a porta 3001 você vir uma versão sem a Banca ou com design antigo:
1. Pressione **Ctrl + F5** (ou **Ctrl + Shift + R**) para forçar o recarregamento total do cache.
2. O sistema de Cache (PWA) foi desativado no `vite.config.js` para evitar esse conflito.

### "Porta 3001 em uso"
Se o Vite tentar abrir na porta 3002, significa que há um processo "zumbi" na 3001.
- **Windows (PowerShell):** `Get-NetTCPConnection -LocalPort 3001 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`

---
*Atualizado em: 22/01/2026 (Eagle Elite Update)*
