import sys
import os
import time
import io

# UTF-8 fix for Windows
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.signal_generator import SignalGenerator
from services.indicator_calculator import analyze_candles
from config import PAIR_LIMIT, ML_ENABLED, LLM_ENABLED, SNIPER_DECOUPLING_THRESHOLD, SNIPER_BEST_SCORE_THRESHOLD

def run_diagnostic():
    print("="*60)
    print("DETAILED SIGNAL DIAGNOSTIC")
    print("="*60)
    
    generator = SignalGenerator()
    
    print("\n[STEP 1] Fetching Market Context (BTC)...")
    generator.current_btc_candles = generator.client.get_klines("BTCUSDT", "30", 100)
    btc_4h = generator.client.get_klines("BTCUSDT", "240", 50)
    generator.current_btc_regime, generator.current_regime_details = generator.btc_tracker.detect_regime(
        generator.current_btc_candles, btc_4h
    )
    print(f"BTC Regime: {generator.current_btc_regime}")

    top_pairs = generator.client.get_top_pairs(10)
    
    for symbol in top_pairs[:5]:
        print("\n" + "-"*40)
        print(f"ANALYZING {symbol}...")
        
        # 1. Fetch data
        candles_30m = generator.client.get_klines(symbol, "30", 100)
        candles_4h = generator.client.get_klines(symbol, "240", 60)
        trades = generator.client.get_recent_trades(symbol, 100)
        oi_data = generator.client.get_open_interest(symbol, "30min", 10)
        lsr_data = generator.client.get_long_short_ratio(symbol, "30min", 10)
        
        # 2. Run raw analysis
        analysis = analyze_candles(
            candles_30m, 
            candles_4h, 
            recent_trades=trades,
            oi_data=oi_data,
            lsr_data=lsr_data,
            btc_candles=generator.current_btc_candles
        )
        
        trend_4h = analysis["trend_4h"]["direction"]
        print(f"  4H Trend: {trend_4h}")
        
        # 3. Check raw signals from indicator_calculator
        ema_sig = analysis["ema"]["signal"]
        pb_sig = analysis["pullback"]["signal"]
        rsi_sig = analysis["rsi_bb"]["signal"]
        js_sig = analysis["institutional"]["judas_signal"]
        
        print(f"  Raw Signals:")
        print(f"    - EMA Crossover: {ema_sig}")
        print(f"    - Trend Pullback: {pb_sig}")
        print(f"    - RSI/BB Reversal: {rsi_sig}")
        print(f"    - Judas Swing: {js_sig}")
        
        # 4. Check if signal_generator would accept them
        if not any([ema_sig, pb_sig, rsi_sig, js_sig]):
            print(f"  ❌ No raw technical patterns detected.")
        else:
            # Check 4H alignment for EMA/PB/JS
            for sig_type, sig in [("EMA", ema_sig), ("Pullback", pb_sig), ("Judas", js_sig)]:
                if sig:
                    aligned = (sig == "LONG" and trend_4h == "UPTREND") or (sig == "SHORT" and trend_4h == "DOWNTREND")
                    if not aligned:
                        print(f"  ⚠️ {sig_type} {sig} rejected: Not aligned with 4H {trend_4h}")
                    else:
                        print(f"  ✅ {sig_type} {sig} is aligned with 4H Trend")

        # 5. Check Score if any signal exists
        # In a real run, generator.analyze_pair would calculate the score.
        # Let's run it to see the score even if it's below threshold in a real run.
        full_signal = generator.analyze_pair(symbol)
        if full_signal:
            print(f"  FINAL SIGNAL: {full_signal['direction']} (Score: {full_signal['score']:.1f})")
            print(f"  Breakdown: {full_signal['breakdown']}")

if __name__ == "__main__":
    run_diagnostic()
