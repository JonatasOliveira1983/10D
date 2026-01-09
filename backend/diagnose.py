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
    
    # SMA Analysis
    print(f"\n--- SMA 8/21 ---")
    sma_fast = analysis['sma']['details'].get('sma_fast', 0)
    sma_slow = analysis['sma']['details'].get('sma_slow', 0)
    print(f"SMA 8:  ${sma_fast:,.2f}")
    print(f"SMA 21: ${sma_slow:,.2f}")
    
    if sma_fast and sma_slow:
        diff = ((sma_fast - sma_slow) / sma_slow) * 100
        position = "ACIMA" if sma_fast > sma_slow else "ABAIXO"
        print(f"SMA 8 esta {position} da SMA 21 ({diff:+.2f}%)")
    
    sma_signal = analysis['sma']['signal']
    if sma_signal:
        print(f">>> CRUZAMENTO DETECTADO: {sma_signal} <<<")
    else:
        print("Nenhum cruzamento no ultimo candle")
    
    # Volume
    print(f"\n--- Volume ---")
    vol = analysis['volume']['details']
    print(f"Volume Atual: {vol.get('current_volume', 0):,.0f}")
    print(f"Volume Medio: {vol.get('avg_volume', 0):,.0f}")
    print(f"Ratio: {vol.get('volume_ratio', 0):.2f}x")
    print(f"Confirmado (>=1.5x): {'SIM' if analysis['volume']['confirmed'] else 'NAO'}")
    
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
    if sma_signal and analysis['volume']['confirmed']:
        print(">>> SINAL SERIA GERADO! <<<")
    elif sma_signal and not analysis['volume']['confirmed']:
        print("Cruzamento detectado MAS volume nao confirmou")
    else:
        print("Sem cruzamento SMA no momento - aguardando...")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    print("\n" + "="*60)
    print("  10D - Sistema de Diagnostico")
    print("="*60)
    
    for pair in pairs:
        diagnose_pair(pair)
