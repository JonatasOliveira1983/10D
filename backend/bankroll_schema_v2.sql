-- ============================================================
-- 10D TRADING SYSTEM - EVOLVED BANKROLL SCHEMA (V2)
-- Execute este script no SQL Editor do Supabase para um RESET TOTAL
-- ============================================================

-- Remover tabelas antigas para evitar conflito de tipos/ID
DROP TABLE IF EXISTS bankroll_trades CASCADE;
DROP TABLE IF EXISTS bankroll_status CASCADE;

-- 1. Tabela de Status da Banca (Saldo e Ciclos)
CREATE TABLE bankroll_status (
    id TEXT PRIMARY KEY DEFAULT 'elite_bankroll',
    current_balance FLOAT DEFAULT 20.0,
    base_balance FLOAT DEFAULT 20.0, -- Saldo no início do ciclo de 20 trades
    entry_size_usd FLOAT DEFAULT 1.0, -- 5% da base_balance (5% de $20 = $1)
    trades_in_cycle INTEGER DEFAULT 0, -- Contador de 0 a 20
    total_trades INTEGER DEFAULT 0,
    cycle_number INTEGER DEFAULT 1,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inserir estado inicial (Reset para $20)
INSERT INTO bankroll_status (id, current_balance, base_balance, entry_size_usd)
VALUES ('elite_bankroll', 20.0, 20.0, 1.0);

-- 2. Tabela de Histórico de Trades da Banca
CREATE TABLE bankroll_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    entry_size_usd FLOAT NOT NULL,
    leverage INTEGER DEFAULT 50,
    pnl_usd FLOAT,
    roi_pct FLOAT,
    status TEXT DEFAULT 'OPEN', -- 'OPEN', 'WON', 'LOST', 'FECHADO PELO CAPITÃO'
    telemetry TEXT, -- Comentário tático do Capitão
    cycle_number INTEGER,
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    signal_id TEXT -- Referência ao sinal original
);

-- 3. Tabela de Memória de Aprendizado do Capitão (ML)
CREATE TABLE IF NOT EXISTS agent_learning (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    insight_type TEXT NOT NULL, -- 'TACTICAL_ADJUSTMENT', 'LOSS_ANALYSIS'
    lesson_learned TEXT NOT NULL,
    context_data JSONB, 
    experience_points_gained INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabela de Subscrições Push (PWA)
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id TEXT DEFAULT 'default_user',
    subscription_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, subscription_data)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_bankroll_trades_status ON bankroll_trades(status);
CREATE INDEX IF NOT EXISTS idx_agent_learning_symbol ON agent_learning(symbol);

-- Refresh do schema
NOTIFY pgrst, 'reload schema';
