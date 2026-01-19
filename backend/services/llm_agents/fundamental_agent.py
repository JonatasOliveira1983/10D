from typing import Dict, Any
from .base_agent import BaseAgent

class FundamentalAgent(BaseAgent):
    """
    The Sentinel.
    Analyzes News Sentiment (Fear & Greed) and Macro Context (BTC Regime).
    Protects against trading against the narrative.
    """
    
    def __init__(self):
        super().__init__(name="Fundamental Agent", role="Macro Sentinel")
        
    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        btc_regime = market_context.get("btc_regime", "Unknown")
        sentiment_score = market_context.get("sentiment_score", 50)
        sentiment_summary = market_context.get("sentiment_summary", "Neutral")
        
        score = 50
        reasoning = []
        
        # 1. BTC Regime Impact
        if btc_regime == "TRENDING":
            score += 10
            reasoning.append("BTC Trending (Favorable)")
        elif btc_regime == "DUMP" or btc_regime == "CRASH":
            score -= 40
            reasoning.append("BTC Crash Detected (Dangerous)")
        elif btc_regime == "RANGING":
            score -= 5
            reasoning.append("BTC Ranging (Choppy)")

        # 2. Sentiment Score Impact (0-100)
        # Low score = Extreme Fear (Bad for Longs, Good for Shorts?)
        direction = signal.get("direction", "LONG")
        
        if direction == "LONG":
            if sentiment_score < 30:
                score -= 30
                reasoning.append(f"Market in Fear ({sentiment_score}) - Bad for Longs")
            elif sentiment_score > 60:
                score += 20
                reasoning.append(f"Market Optimism ({sentiment_score}) - Good for Longs")
        elif direction == "SHORT":
            if sentiment_score > 70:
                score -= 30
                reasoning.append(f"Market Greed ({sentiment_score}) - Bad for Shorts")
            elif sentiment_score < 40:
                score += 20
                reasoning.append(f"Market Weakness ({sentiment_score}) - Good for Shorts")
                
        # Final Verdict
        final_verdict = "NEUTRAL"
        if score >= 65: final_verdict = "APPROVED"
        elif score <= 35: final_verdict = "REJECTED"
        
        return {
            "agent": self.name,
            "score": min(100, max(0, score)),
            "verdict": final_verdict,
            "reasoning": "; ".join(reasoning),
            "metadata": {"sentiment_summary": sentiment_summary}
        }
