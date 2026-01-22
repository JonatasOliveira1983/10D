import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm_trading_brain import LLMTradingBrain


    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("🧠 TESTING THE COUNCIL DEBATE\n")
        f.write("="*60 + "\n")
        
        # Initialize Brain
        config = {
            "LLM_MODEL": "gemini-1.5-flash",
            "LLM_MIN_CONFIDENCE": 0.6
        }
        brain = LLMTradingBrain(config)
        
        if not brain.is_enabled():
            f.write("❌ LLM not enabled. Check GEMINI_API_KEY.\n")
            return

        # Scenario 1: Perfect Trade
        f.write("\n--- SCENARIO 1: The Perfect Long ---\n")
        signal_good = {
            "symbol": "BTCUSDT",
            "direction": "LONG",
            "entry_price": 65000,
            "take_profit": 67000, # +3%
            "stop_loss": 64350,   # -1%
            "signal_type": "TREND_PULLBACK",
            "score": 95,
            "volume_ratio": 2.5,
            "indicators": {"rsi": 40},
            "dynamic_targets": {"tp_pct": 3.0, "sl_pct": 1.0}
        }
        context_good = {
            "btc_regime": "TRENDING",
            "sentiment_score": 75, # Greed
            "sentiment_summary": "Market is bullish on ETF news."
        }
        
        result = brain.validate_signal_context(signal_good, context_good)
        f.write(f"Verdict: {'✅ APPROVED' if result['approved'] else '❌ REJECTED'}\n")
        f.write(f"Reasoning: {result.get('reasoning')}\n")
        if 'vote_breakdown' in result:
            f.write(f"Votes: {result['vote_breakdown']}\n")

        # Scenario 2: The Suicide Short
        f.write("\n--- SCENARIO 2: The Suicide Short (Bad Sentiment + Bad R:R) ---\n")
        signal_bad = {
            "symbol": "MEMEUSDT",
            "direction": "SHORT",
            "entry_price": 1.0,
            "take_profit": 0.99, # +1%
            "stop_loss": 1.05,   # -5% (Terrible R:R)
            "signal_type": "RSI_REVERSAL",
            "score": 60,
            "volume_ratio": 0.5,
            "indicators": {"rsi": 80},
            "dynamic_targets": {"tp_pct": 1.0, "sl_pct": 5.0} # 0.2 R:R
        }
        context_bad = {
            "btc_regime": "BREAKOUT", # Don't short breakouts
            "sentiment_score": 80, # Extreme Greed (Don't short)
            "sentiment_summary": "Retail is aping into memes."
        }
        
        result = brain.validate_signal_context(signal_bad, context_bad)
        f.write(f"Verdict: {'✅ APPROVED' if result['approved'] else '❌ REJECTED'}\n")
        f.write(f"Reasoning: {result.get('reasoning')}\n")
        if 'vote_breakdown' in result:
            f.write(f"Votes: {result['vote_breakdown']}\n")


if __name__ == "__main__":
    try:
        test_council_debate()
    except Exception as e:
        with open("test_result.txt", "a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL ERROR: {str(e)}\n")
            import traceback
            traceback.print_exc(file=f)
