-- ============================================================
-- 10D TRADING SYSTEM - SUPABASE SCHEMA
-- Execute este script no SQL Editor do Supabase
-- Criado em: 2026-01-19
-- ============================================================

-- ============================================================
-- TABELA: signals
-- Armazena todos os sinais de trading gerados pelo sistema
-- ============================================================

-- Criar tabela se não existir
CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    signal_type TEXT,
    entry_price FLOAT,
    stop_loss FLOAT,
    take_profit FLOAT,
    score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',
    final_roi INTEGER,
    timestamp BIGINT,
    exit_timestamp BIGINT,
    highest_roi FLOAT DEFAULT 0.0,
    partial_tp_hit BOOLEAN DEFAULT FALSE,
    trailing_stop_active BOOLEAN DEFAULT FALSE,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Adicionar colunas que podem estar faltando (seguro para executar múltiplas vezes)
ALTER TABLE signals ADD COLUMN IF NOT EXISTS highest_roi FLOAT DEFAULT 0.0;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS partial_tp_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS trailing_stop_active BOOLEAN DEFAULT FALSE;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS exit_timestamp BIGINT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS signal_type TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE signals ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_direction ON signals(direction);

-- ============================================================
-- TABELA: trading_plan
-- Armazena o plano de trading configurado pelo usuário
-- ============================================================

CREATE TABLE IF NOT EXISTS trading_plan (
    user_id TEXT PRIMARY KEY DEFAULT 'default_user',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: llm_insights (NOVA - para o sistema LLM)
-- Armazena insights e aprendizados do LLM Trading Brain
-- ============================================================

CREATE TABLE IF NOT EXISTS llm_insights (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    insight_type TEXT NOT NULL, -- 'trade_result', 'pattern_learned', 'council_decision'
    content JSONB NOT NULL,
    confidence FLOAT,
    outcome TEXT, -- 'success', 'failure', 'pending'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para llm_insights
CREATE INDEX IF NOT EXISTS idx_llm_insights_symbol ON llm_insights(symbol);
CREATE INDEX IF NOT EXISTS idx_llm_insights_type ON llm_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_llm_insights_created ON llm_insights(created_at DESC);

-- ============================================================
-- TABELA: rag_memory (NOVA - para memória visual/RAG)
-- Cache de embeddings e padrões históricos
-- ============================================================

CREATE TABLE IF NOT EXISTS rag_memory (
    id SERIAL PRIMARY KEY,
    pattern_hash TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_conditions JSONB,
    outcome TEXT NOT NULL, -- 'TP_HIT', 'SL_HIT', 'EXPIRED'
    roi FLOAT,
    embedding VECTOR(768), -- Se usar pgvector, senão JSONB
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fallback se VECTOR não suportado (usar JSONB)
-- ALTER TABLE rag_memory ADD COLUMN IF NOT EXISTS embedding_json JSONB;

-- Índices para rag_memory
CREATE INDEX IF NOT EXISTS idx_rag_memory_symbol ON rag_memory(symbol);
CREATE INDEX IF NOT EXISTS idx_rag_memory_outcome ON rag_memory(outcome);
CREATE INDEX IF NOT EXISTS idx_rag_memory_hash ON rag_memory(pattern_hash);

-- ============================================================
-- TABELA: council_decisions (NOVA - para auditoria do Council)
-- Registro das decisões do LLM Council
-- ============================================================

CREATE TABLE IF NOT EXISTS council_decisions (
    id SERIAL PRIMARY KEY,
    signal_id TEXT REFERENCES signals(id),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    
    -- Votos dos agentes
    technical_vote TEXT, -- 'APPROVE', 'REJECT', 'NEUTRAL'
    technical_score INTEGER,
    technical_reason TEXT,
    
    risk_vote TEXT,
    risk_score INTEGER,
    risk_reason TEXT,
    
    fundamental_vote TEXT,
    fundamental_score INTEGER,
    fundamental_reason TEXT,
    
    -- Decisão final
    final_decision TEXT NOT NULL, -- 'APPROVED', 'REJECTED'
    final_confidence INTEGER,
    final_reasoning TEXT,
    
    -- Resultado real (preenchido após finalização)
    actual_outcome TEXT, -- 'TP_HIT', 'SL_HIT', 'EXPIRED'
    actual_roi FLOAT,
    decision_accuracy BOOLEAN, -- TRUE se decisão foi correta
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para council_decisions
CREATE INDEX IF NOT EXISTS idx_council_symbol ON council_decisions(symbol);
CREATE INDEX IF NOT EXISTS idx_council_decision ON council_decisions(final_decision);
CREATE INDEX IF NOT EXISTS idx_council_accuracy ON council_decisions(decision_accuracy);
CREATE INDEX IF NOT EXISTS idx_council_created ON council_decisions(created_at DESC);

-- ============================================================
-- TABELA: ml_training_log (NOVA - log de treinamentos ML)
-- ============================================================

CREATE TABLE IF NOT EXISTS ml_training_log (
    id SERIAL PRIMARY KEY,
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    samples_count INTEGER,
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    top_features JSONB,
    model_version TEXT,
    notes TEXT
);

-- ============================================================
-- VIEWS ÚTEIS
-- ============================================================

-- View: Performance por símbolo
CREATE OR REPLACE VIEW signal_performance_by_symbol AS
SELECT 
    symbol,
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'TP_HIT' THEN 1 END) as wins,
    COUNT(CASE WHEN status = 'SL_HIT' THEN 1 END) as losses,
    ROUND(
        COUNT(CASE WHEN status = 'TP_HIT' THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(CASE WHEN status IN ('TP_HIT', 'SL_HIT') THEN 1 END), 0) * 100, 
        2
    ) as win_rate,
    ROUND(AVG(CASE WHEN final_roi IS NOT NULL THEN final_roi ELSE 0 END)::NUMERIC, 2) as avg_roi
FROM signals
WHERE status IN ('TP_HIT', 'SL_HIT', 'EXPIRED')
GROUP BY symbol
ORDER BY total_trades DESC;

-- View: Performance diária
CREATE OR REPLACE VIEW daily_performance AS
SELECT 
    DATE(to_timestamp(timestamp/1000)) as trade_date,
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'TP_HIT' THEN 1 END) as wins,
    COUNT(CASE WHEN status = 'SL_HIT' THEN 1 END) as losses,
    SUM(CASE WHEN final_roi IS NOT NULL THEN final_roi ELSE 0 END) as total_roi
FROM signals
WHERE status IN ('TP_HIT', 'SL_HIT', 'EXPIRED')
  AND timestamp IS NOT NULL
GROUP BY DATE(to_timestamp(timestamp/1000))
ORDER BY trade_date DESC;

-- ============================================================
-- Row Level Security (RLS) - Opcional
-- Descomente se precisar de segurança por usuário
-- ============================================================

-- ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trading_plan ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- FUNÇÕES ÚTEIS
-- ============================================================

-- Função para limpar sinais antigos (manter últimos 30 dias)
CREATE OR REPLACE FUNCTION cleanup_old_signals(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM signals 
    WHERE status != 'ACTIVE' 
    AND timestamp < (EXTRACT(EPOCH FROM NOW() - INTERVAL '1 day' * days_to_keep) * 1000);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Função para recalcular estatísticas
CREATE OR REPLACE FUNCTION recalc_symbol_stats(target_symbol TEXT)
RETURNS TABLE(wins BIGINT, losses BIGINT, win_rate NUMERIC, avg_roi NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(CASE WHEN s.status = 'TP_HIT' THEN 1 END) as wins,
        COUNT(CASE WHEN s.status = 'SL_HIT' THEN 1 END) as losses,
        ROUND(
            COUNT(CASE WHEN s.status = 'TP_HIT' THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(CASE WHEN s.status IN ('TP_HIT', 'SL_HIT') THEN 1 END), 0) * 100, 
            2
        ) as win_rate,
        ROUND(AVG(CASE WHEN s.final_roi IS NOT NULL THEN s.final_roi ELSE 0 END)::NUMERIC, 2) as avg_roi
    FROM signals s
    WHERE s.symbol = target_symbol
    AND s.status IN ('TP_HIT', 'SL_HIT', 'EXPIRED');
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PERMISSÕES (para API pública)
-- ============================================================

-- Permitir acesso anônimo (ajuste conforme necessidade)
GRANT ALL ON signals TO anon;
GRANT ALL ON trading_plan TO anon;
GRANT ALL ON llm_insights TO anon;
GRANT ALL ON rag_memory TO anon;
GRANT ALL ON council_decisions TO anon;
GRANT ALL ON ml_training_log TO anon;

-- Sequências
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- ============================================================
-- FINALIZAÇÃO
-- ============================================================

-- Refresh do schema cache do PostgREST (resolve o erro 'column not found in schema cache')
NOTIFY pgrst, 'reload schema';

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '10D Trading System - Schema atualizado com sucesso!';
    RAISE NOTICE 'Tabelas: signals, trading_plan, llm_insights, rag_memory, council_decisions, ml_training_log';
    RAISE NOTICE '============================================================';
END $$;
