"""
Test script for LLM Trading Brain
Run: python test_llm_brain.py
"""

import os
import sys

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_llm_brain():
    print("=" * 60)
    print("🧠 LLM Trading Brain Test")
    print("=" * 60)
    
    # 1. Test import
    print("\n[1] Testing import...")
    try:
        from services.llm_trading_brain import LLMTradingBrain
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return
    
    # 2. Test initialization
    print("\n[2] Testing initialization...")
    try:
        from config import LLM_MODEL, LLM_CACHE_TTL_SECONDS, LLM_MIN_CONFIDENCE
        config = {
            "LLM_MODEL": LLM_MODEL,
            "LLM_CACHE_TTL_SECONDS": LLM_CACHE_TTL_SECONDS,
            "LLM_MIN_CONFIDENCE": LLM_MIN_CONFIDENCE
        }
        brain = LLMTradingBrain(config)
        print(f"✅ Initialization successful")
        print(f"   Model enabled: {brain.is_enabled()}")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # 3. Test connection
    print("\n[3] Testing Gemini connection...")
    try:
        result = brain.test_connection()
        print(f"   Status: {result.get('status')}")
        if result.get('status') == 'OK':
            print(f"✅ Connection successful")
            print(f"   Response: {result.get('response', '')[:50]}...")
        else:
            print(f"⚠️ Connection issue: {result.get('message')}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    # 4. Test signal validation
    print("\n[4] Testing signal validation...")
    try:
        mock_signal = {
            "symbol": "ETHUSDT",
            "direction": "LONG",
            "entry_price": 3500.0,
            "take_profit": 3570.0,
            "stop_loss": 3465.0,
            "signal_type": "EMA_CROSSOVER",
            "score": 85.0,
            "ml_probability": 0.72,
            "rsi": 45,
            "trend": "UPTREND",
            "dynamic_targets": {"tp_pct": 2.0, "sl_pct": 1.0}
        }
        
        market_context = {
            "btc_regime": "TRENDING",
            "decoupling_score": 0.35
        }
        
        validation = brain.validate_signal_context(mock_signal, market_context)
        print(f"   Approved: {validation.get('approved')}")
        print(f"   Confidence: {validation.get('confidence', 0):.0%}")
        print(f"   Action: {validation.get('suggested_action')}")
        print(f"   Reasoning: {validation.get('reasoning', '')[:60]}...")
        print("✅ Validation test complete")
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
    
    # 5. Test TP optimization
    print("\n[5] Testing TP optimization...")
    try:
        tp_result = brain.suggest_optimal_tp(mock_signal, market_context)
        print(f"   Original TP: {tp_result.get('original_tp_pct')}%")
        print(f"   Suggested TP: {tp_result.get('suggested_tp_pct')}%")
        print(f"   Should adjust: {tp_result.get('should_adjust')}")
        print(f"   Reasoning: {tp_result.get('reasoning', '')[:50]}...")
        print("✅ TP optimization test complete")
    except Exception as e:
        print(f"❌ TP optimization test failed: {e}")
    
    # 6. Test exit analysis
    print("\n[6] Testing exit analysis...")
    try:
        market_momentum = {"trend": "BULLISH", "volume_status": "HIGH"}
        exit_result = brain.analyze_exit_opportunity(mock_signal, 2.5, market_momentum)
        print(f"   Action: {exit_result.get('action')}")
        print(f"   Confidence: {exit_result.get('confidence', 0):.0%}")
        print(f"   Reasoning: {exit_result.get('reasoning', '')[:50]}...")
        print("✅ Exit analysis test complete")
    except Exception as e:
        print(f"❌ Exit analysis test failed: {e}")
    
    # 7. Get status
    print("\n[7] Brain status:")
    try:
        status = brain.get_status()
        print(f"   Enabled: {status.get('enabled')}")
        print(f"   Model: {status.get('model')}")
        print(f"   Total requests: {status.get('stats', {}).get('total_requests', 0)}")
        print(f"   Cache hits: {status.get('stats', {}).get('cache_hits', 0)}")
        print("✅ Status retrieved")
    except Exception as e:
        print(f"❌ Status failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All tests complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_llm_brain()
