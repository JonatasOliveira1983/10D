from typing import Dict, Any
from .base_agent import BaseAgent

class RiskAgent(BaseAgent):
    """
    The Guardian.
    Focuses on Risk Management, Stop Loss distance, and R:R ratio.
    It vetoes trades that expose the account too much.
    """
    
    def __init__(self):
        super().__init__(name="Risk Agent", role="Risk Manager")
        
    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        entry = signal.get("entry_price", 0)
        tp = signal.get("take_profit", 0)
        sl = signal.get("stop_loss", 0)
        
        if entry == 0:
            return {"agent": self.name, "score": 0, "verdict": "REJECTED", "reasoning": "Invalid prices"}
            
        # Calculate Percentages
        tp_pct = abs((tp - entry) / entry) * 100
        sl_pct = abs((entry - sl) / entry) * 100
        
        score = 60 # Start neutral-positive
        reasoning = []
        
        # 1. Risk/Reward Ratio (Desired > 1.5)
        if sl_pct > 0:
            risk_reward = tp_pct / sl_pct
            if risk_reward >= 2.0:
                score += 20
                reasoning.append(f"Excellent R:R ({risk_reward:.1f})")
            elif risk_reward < 1.0:
                score -= 30
                reasoning.append(f"Poor R:R ({risk_reward:.1f})")
        
        # 2. Stop Loss size (Too tight = noise, Too wide = huge risk)
        if sl_pct > 3.0:
            score -= 20
            reasoning.append(f"Stop Loss too wide ({sl_pct:.1f}%)")
        elif sl_pct < 0.3:
            score -= 10
            reasoning.append(f"Stop Loss too tight ({sl_pct:.1f}%)")
            
        # Final Verdict
        final_verdict = "NEUTRAL"
        if score >= 70: final_verdict = "APPROVED"
        elif score <= 40: final_verdict = "REJECTED"
        
        return {
            "agent": self.name,
            "score": min(100, max(0, score)),
            "verdict": final_verdict,
            "reasoning": "; ".join(reasoning)
        }
