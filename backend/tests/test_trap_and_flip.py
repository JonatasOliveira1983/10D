import sys
import os
import json
import time
from unittest.mock import MagicMock

# Mocking a minimal environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.signal_generator import SignalGenerator

def test_trap_and_flip():
    print("🚀 Starting TRAP & FLIP Verification Test...")
    
    # 1. Setup Generator with Mocks
    gen = SignalGenerator()
    gen.client = MagicMock()
    gen.db = MagicMock()
    gen.llm_brain = MagicMock()
    
    symbol = "BIOUSDT.P"
    entry_price = 1.0
    
    # Simulate an active LONG signal
    signal = {
        "id": f"{symbol}_123",
        "symbol": symbol,
        "direction": "LONG",
        "entry_price": entry_price,
        "take_profit": 1.06, # 6% Sniper
        "stop_loss": 0.98,
        "timestamp": int(time.time() * 1000) - 400000, # 6 minutes ago
        "score": 100,
        "is_sniper": True,
        "status": "ACTIVE"
    }
    gen.active_signals = {symbol: signal}
    
    # 2. Mock Ticker (Price dropped slightly)
    gen.client.get_all_tickers.return_value = [
        {"symbol": symbol, "lastPrice": "0.995"}
    ]
    
    # 3. Mock LLM Responses for Scout & Sentinel (TRAP!!)
    def mock_call(p):
        if "Scout" in p:
            return json.dumps({
                "bias_health_score": 0.2,
                "status": "TRAP_DETECTED",
                "reasoning": "Preço falhou em romper máxima e está perdendo suporte.",
                "suggested_action": "FLIP_IF_BREAKS",
                "flip_trigger_price": 0.99
            })
        if "Sentinel" in p:
            return json.dumps({
                "liquidity_conviction": 0.1,
                "flow_status": "MANIPULATION",
                "reasoning": "Absorção institucional massiva no book.",
                "trap_probability": 0.9,
                "action": "ABORT_AND_FLIP"
            })
        return "{}"

    gen.llm_brain.call_gemini = mock_call
    gen.llm_brain.call_gemini.side_effect = None # Clear if any
    
    # Mock analyze_pair for the reverse trade
    gen.analyze_pair = MagicMock()
    gen.analyze_pair.return_value = {
        "symbol": symbol,
        "direction": "SHORT",
        "entry_price": 0.995,
        "take_profit": 0.93,
        "stop_loss": 1.01,
        "score": 100,
        "is_sniper": True,
        "status": "ACTIVE"
    }

    # 4. RUN MONITOR
    print(f"Checking {symbol} for Traps...")
    gen.monitor_active_signals()
    
    # 5. VERIFY
    # The original LONG should be removed from active and moved to history as FLIPPED
    # A new SHORT should be in active_signals
    
    assert symbol in gen.active_signals
    final_sig = gen.active_signals[symbol]
    
    print("\nFINAL SCAN RESULT:")
    print(f"Symbol: {symbol}")
    print(f"New Direction: {final_sig['direction']}")
    print(f"Is Flip: {final_sig.get('is_flip')}")
    
    assert final_sig["direction"] == "SHORT"
    assert final_sig.get("is_flip") == True
    
    print("\n✅ Verification Successful: Trap detected and trade flipped!")

if __name__ == "__main__":
    try:
        test_trap_and_flip()
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
