-- ============================================================
-- 10D TRADING SYSTEM - BANKROLL SCHEMA V3 (Risk Management Update)
-- Executar no SQL Editor do Supabase
-- ============================================================

-- Adicionar coluna stop_loss para rastrear ordens Risk-Free
ALTER TABLE bankroll_trades 
ADD COLUMN IF NOT EXISTS stop_loss FLOAT;

-- Atualizar stop_loss para ordens abertas (baseado no preço de entrada e direção)
-- Isso é uma estimativa segura (1% SL) caso não tenhamos o dado histórico
UPDATE bankroll_trades
SET stop_loss = CASE 
    WHEN direction = 'LONG' THEN entry_price * 0.99 
    ELSE entry_price * 1.01 
END
WHERE stop_loss IS NULL AND status = 'OPEN';

-- Notificar reload
NOTIFY pgrst, 'reload schema';
