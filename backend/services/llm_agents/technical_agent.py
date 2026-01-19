from typing import Dict, Any
from .base_agent import BaseAgent
import json
from services.rag_memory import RAGMemory

class TechnicalAgent(BaseAgent):
    """
    The Chartist.
    Focuses purely on Price Action, Indicators, and Statistical Probabilities.
    It ignores news and PnL.
    """
    
    def __init__(self, rag_memory=None):
        super().__init__(name="Technical Agent", role="Expert Chartist")
        if rag_memory:
            self.memory = rag_memory
        else:
            self.memory = RAGMemory(storage_path="data/memory_index.json")
        
    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        # Extract technical data (safe access)
        symbol = signal.get("symbol", "Unknown")
        indicators = signal.get("indicators", {})
        rsi = indicators.get("rsi", 50)
        adx = indicators.get("adx", 0) # Assumed available or 0
        volume_ratio = signal.get("volume_ratio", 1.0)
        btc_regime = market_context.get("btc_regime", "Unknown")
        
        # Heuristic Logic (Can be replaced by LLM call later for deeper analysis)
        score = 50
        reasoning = []
        
        # 1. Trend Alignment
        if signal.get("direction") == "LONG":
            if btc_regime == "TRENDING" or btc_regime == "BREAKOUT":
                score += 20
                reasoning.append("Aligned with BTC Trend/Breakout")
            elif btc_regime == "DUMP":
                score -= 30
                reasoning.append("Fighting BTC Dump (Risky)")
        
        # 2. RSI Check
        if signal.get("direction") == "LONG":
            if rsi < 30: 
                score += 15
                reasoning.append("Oversold RSI (Good entry)")
            elif rsi > 70:
                score -= 10
                reasoning.append("Overbought RSI (Chasing tops)")
                
        # 3. Volume Check
            score -= 10
            reasoning.append("Weak Volume")
            
        # 4. RAG Memory Check (The Ghost of Trades Past)
        similar_trades = self.memory.find_similar(signal, k=5)
        if similar_trades:
            # Calculate win rate of similar trades
            wins = sum(1 for t in similar_trades if t["metadata"]["outcome"].get("status") == "TP_HIT")
            total = len(similar_trades)
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            if win_rate > 60:
                score += 15
                reasoning.append(f"Historical Pattern Match: {win_rate:.0f}% WR (Bullish Memory)")
            elif win_rate < 30:
                score -= 20
                reasoning.append(f"Historical Pattern Match: {win_rate:.0f}% WR (Bearish Memory)")
            else:
                reasoning.append(f"Historical Pattern Match: {win_rate:.0f}% WR (Neutral Memory)")
            
        # Final Verification
        final_verdict = "NEUTRAL"
        if score >= 75: final_verdict = "APPROVED"
        elif score <= 40: final_verdict = "REJECTED"
        
        return {
            "agent": self.name,
            "score": min(100, max(0, score)),
            "verdict": final_verdict,
            "reasoning": "; ".join(reasoning)
        }
