import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adiciona o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.signal_generator import SignalGenerator
import config

class TestSmartExitsV3(unittest.TestCase):
    def setUp(self):
        # Mock do BD e Bybit para evitar chamadas reais
        self.patcher_db = patch('services.database_manager.DatabaseManager')
        self.patcher_bybit = patch('services.bybit_client.BybitClient')
        self.mock_db = self.patcher_db.start()
        self.mock_bybit = self.patcher_bybit.start()
        
        # Desabilita ML e LLM para simplicidade do teste
        with patch('services.signal_generator.ML_ENABLED', False), \
             patch('services.signal_generator.LLM_ENABLED', False):
            self.generator = SignalGenerator()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_bybit.stop()

    def test_surf_logic_and_trailing_stop(self):
        """Valida Breakeven -> Trailing -> Surf (Ignorar TP)"""
        symbol = "BTCUSDT"
        entry_price = 100.0
        tp_6pct = 106.0
        sl_1pct = 99.0
        
        # 1. Simular um sinal ativo Sniper
        import time
        signal = {
            "symbol": symbol,
            "direction": "LONG",
            "entry_price": entry_price,
            "take_profit": tp_6pct,
            "stop_loss": sl_1pct,
            "is_sniper": True,
            "partial_tp_hit": False,
            "trailing_stop_active": False,
            "highest_roi": 0.0,
            "timestamp": int(time.time() * 1000),
            "status": "ACTIVE"
        }
        self.generator.active_signals = {symbol: signal}
        
        # 2. Mock do preço subindo para 2% (Breakeven)
        mock_ticker = {"symbol": symbol, "lastPrice": "102.0", "tickSize": "0.1"}
        self.generator.client.get_all_tickers = MagicMock(return_value=[mock_ticker])
        
        # Executa monitoramento
        self.generator.monitor_active_signals()
        
        # Verifica Breakeven
        self.assertTrue(signal["partial_tp_hit"])
        self.assertEqual(signal["stop_loss"], 100.0) # SL movido para entrada
        print("--- Breakeven em 2% validado.")

        # 3. Mock do preço subindo para 3% (Trailing Stop Ativado)
        mock_ticker["lastPrice"] = "103.0"
        self.generator.monitor_active_signals()
        
        self.assertTrue(signal["trailing_stop_active"])
        # SL deve estar em 103 * 0.99 = 101.97
        self.assertGreater(signal["stop_loss"], 101.9) 
        print(f"--- Trailing Stop em 3% ativado. SL: {signal['stop_loss']}")

        # 4. Mock do preço atingindo o TP de 6% (Surf Logic)
        # O sistema NÃO deve fechar (hit=False) porque o Trailing está ativo
        mock_ticker["lastPrice"] = "106.5"
        self.generator.monitor_active_signals()
        
        # Verificamos se o sinal ainda está ativo (não foi removido da memória)
        self.assertIn(symbol, self.generator.active_signals)
        print("--- Surf Logic validada: TP de 6% ignorado enquanto Trailing está ativo.")
        
        # 5. Preço continua subindo para 10% (110.0)
        mock_ticker["lastPrice"] = "110.0"
        self.generator.monitor_active_signals()
        expected_sl = 110.0 * 0.99 # 108.9
        self.assertAlmostEqual(signal["stop_loss"], 108.9, delta=0.1)
        print(f"--- Surfando até 10%: SL subiu para {signal['stop_loss']}")

        # 6. Preço cai e atinge o Trailing Stop
        mock_ticker["lastPrice"] = "108.0" # Abaixo do SL de 108.9
        
        # Mock para klines verification
        self.generator._verify_with_klines = MagicMock(return_value=(True, "SL_HIT"))
        
        self.generator.monitor_active_signals()
        
        # Sinal deve ser removido após hit
        self.assertNotIn(symbol, self.generator.active_signals)
        print("✅ Saída no Trailing Stop validada com lucro final acumulado.")

if __name__ == '__main__':
    unittest.main()
