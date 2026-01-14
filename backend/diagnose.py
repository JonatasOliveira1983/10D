"""
10D - Diagnostic Script
Analyzes current market state for debugging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.bybit_client import BybitClient
from services.indicator_calculator import analyze_candles
from services.sr_detector import get_all_sr_levels, check_sr_proximity

def diagnose_pair(symbol):
    """Run full diagnosis on a trading pair"""
    client = BybitClient()
    
    print(f"\n{'='*60}")
    print(f"  {symbol} - Diagnostico Completo")
    print(f"{'='*60}")
    
    # Fetch 30M candles
    candles = client.get_klines(symbol, "30", 100)
    if not candles:
        print("ERRO: Nao foi possivel obter candles")
        return
    
    # Analyze
    analysis = analyze_candles(candles)
    
    # Current price
    print(f"\nPreco Atual: ${analysis['current_price']:,.2f}")
    
    # EMA Analysis
    print(f"\n--- EMA 20/50 ---")
    ema_fast = analysis['ema']['details'].get('ema_fast', 0)
    ema_slow = analysis['ema']['details'].get('ema_slow', 0)
    print(f"EMA 20: ${ema_fast:,.2f}")
    print(f"EMA 50: ${ema_slow:,.2f}")
    
    if ema_fast and ema_slow:
        diff = ((ema_fast - ema_slow) / ema_slow) * 100
        position = "ACIMA" if ema_fast > ema_slow else "ABAIXO"
        print(f"EMA 20 esta {position} da EMA 50 ({diff:+.2f}%)")
    
    ema_signal = analysis['ema']['signal']
    if ema_signal:
        print(f">>> CRUZAMENTO EMA DETECTADO: {ema_signal} <<<")
        print(f"Confirmacao MACD: {'SIM' if analysis['ema']['details'].get('macd_confirmed') else 'NAO'}")
    else:
        print("Nenhum cruzamento EMA no ultimo candle")
    
    # MACD 
    print(f"\n--- MACD ---")
    print(f"Histograma: {analysis['macd'].get('histogram', 0):.6f}")

    # Volume
    print(f"\n--- Volume ---")
    vol = analysis['volume']['details']
    print(f"Volume Atual: {vol.get('current_volume', 0):,.0f}")
    print(f"Volume Medio: {vol.get('avg_volume', 0):,.0f}")
    print(f"Ratio: {vol.get('volume_ratio', 0):.2f}x")
    print(f"Confirmado (>=1.2x): {'SIM' if analysis['volume']['confirmed'] else 'NAO'}")
    
    # Pivot Trend
    print(f"\n--- Pivot Point S. Trend ---")
    pivot = analysis['pivot_trend']['details']
    print(f"Banda Superior: ${pivot.get('upper_band', 0):,.2f}")
    print(f"Banda Inferior: ${pivot.get('lower_band', 0):,.2f}")
    print(f"Direcao: {analysis['pivot_trend']['direction'] or 'Neutro'}")
    
    # S/R from Daily
    daily_candles = client.get_klines(symbol, "D", 30)
    if daily_candles:
        sr_levels = get_all_sr_levels(daily_candles)
        proximity = check_sr_proximity(analysis['current_price'], sr_levels)
        
        print(f"\n--- Suporte/Resistencia (1D) ---")
        print(f"Zona Atual: {proximity['zone']}")
        if proximity['nearest_resistance']:
            r = proximity['nearest_resistance']
            dist = proximity['distance_to_resistance'] * 100
            print(f"Resistencia Proxima: {r['name']} @ ${r['level']:,.2f} ({dist:.2f}% distante)")
        if proximity['nearest_support']:
            s = proximity['nearest_support']
            dist = proximity['distance_to_support'] * 100
            print(f"Suporte Proximo: {s['name']} @ ${s['level']:,.2f} ({dist:.2f}% distante)")
    
    # Final verdict
    print(f"\n--- Veredicto ---")
    if ema_signal and analysis['ema']['details'].get('macd_confirmed'):
        print(">>> SINAL EMA + MACD SERIA GERADO! <<<")
    elif ema_signal:
        print("Cruzamento EMA detectado MAS MACD nao confirmou")
    else:
        print("Sem cruzamento EMA no momento - aguardando...")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    print("\n" + "="*60)
    print("  10D - Sistema de Diagnostico")
    print("="*60)
    
    for pair in pairs:
        diagnose_pair(pair)
