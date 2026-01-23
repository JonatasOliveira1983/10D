-- ============================================================
-- 10D TRADING SYSTEM - BANKROLL SCHEMA FINAL (V4)
-- Inclui tabelas do Capitão, Logs de Conversa e Linhas do Gráfico
-- Execute este script no SQL Editor do Supabase para ATUALIZAR/RESETAR
-- ============================================================

-- ⚠️ CUIDADO: Isso apaga todos os dados anteriores (DROP CASCADE)
DROP TABLE IF EXISTS bankroll_trades CASCADE;
DROP TABLE IF EXISTS bankroll_status CASCADE;
DROP TABLE IF EXISTS captain_logs CASCADE;
DROP TABLE IF EXISTS agent_learning CASCADE;
DROP TABLE IF EXISTS push_subscriptions CASCADE;

-- 1. Tabela de Status da Banca (Saldo e Ciclos)
CREATE TABLE bankroll_status (
    id TEXT PRIMARY KEY DEFAULT 'elite_bankroll',
    current_balance FLOAT DEFAULT 20.0,
    base_balance FLOAT DEFAULT 20.0, -- Floor para o cálculo de juros compostos
    entry_size_usd FLOAT DEFAULT 1.0, -- Lote Inicial (ex: 5% da base)
    trades_in_cycle INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    cycle_number INTEGER DEFAULT 1,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Estado Inicial
INSERT INTO bankroll_status (id, current_balance, base_balance, entry_size_usd)
VALUES ('elite_bankroll', 20.0, 20.0, 1.0);

-- 2. Tabela de Histórico de Trades da Banca (Com Linhas do Gráfico)
CREATE TABLE bankroll_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL, -- 'LONG' ou 'SHORT'
    
    -- Dados de Preço e Linhas
    entry_price FLOAT NOT NULL,
    stop_loss FLOAT,   -- 🔴 Linha de SL (Atualizável pelo Capitão)
    take_profit FLOAT, -- 🟢 Linha de TP
    exit_price FLOAT,
    
    -- Dados Financeiros
    entry_size_usd FLOAT NOT NULL,
    leverage INTEGER DEFAULT 50,
    pnl_usd FLOAT,
    roi_pct FLOAT,
    
    -- Status e Controle
    status TEXT DEFAULT 'OPEN', 
    telemetry TEXT, -- Último "pensamento" rápido do Capitão
    cycle_number INTEGER,
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    signal_id TEXT
);

-- 3. [NOVA] Diário de Bordo do Capitão (Logs de Conversa/Decisão)
-- Guarda o histórico de raciocínio para cada trade (ex: "Movi SL para entrada", "Detectei volume alto")
CREATE TABLE captain_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID REFERENCES bankroll_trades(id), -- Link opcional com um trade específico
    symbol TEXT,
    log_type TEXT DEFAULT 'INFO', -- 'ENTRY', 'EXIT', 'RISK_UPDATE', 'THOUGHT'
    message TEXT NOT NULL,
    metadata JSONB, -- Para guardar dados extras (ex: valor do RSI, noticia lida)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Memória de Aprendizado (Longo Prazo/RAG)
CREATE TABLE agent_learning (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    insight_type TEXT NOT NULL, 
    lesson_learned TEXT NOT NULL,
    context_data JSONB, 
    experience_points_gained INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Subscrições Push (PWA)
CREATE TABLE push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id TEXT DEFAULT 'default_user',
    subscription_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, subscription_data)
);

-- Índices de Performance
CREATE INDEX idx_bankroll_trades_status ON bankroll_trades(status);
CREATE INDEX idx_captain_logs_trade_id ON captain_logs(trade_id);
CREATE INDEX idx_captain_logs_created_at ON captain_logs(created_at DESC);

-- Notificar Sistema
NOTIFY pgrst, 'reload schema';
