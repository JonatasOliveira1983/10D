import json
from typing import Dict, Any

class AdaptiveBiasAgent:
    """
    The Scout.
    Analyzes price reaction speed and conviction post-entry.
    If a LONG signal is followed by stagnant or rejecting price action, 
    this agent lowers the bias health and suggests a preemptive exit or flip.
    """
    
    def __init__(self):
        self.name = "Adaptive Bias Scout"

    def analyze_reaction(self, signal: Dict[str, Any], recent_candles: list, llm_call_func: Any) -> Dict[str, Any]:
        """
        Analyzes how the price reacted after the signal 'timestamp'.
        """
        
        prompt = f"""You are the Scout specializing in Price Action Confirmation.
Analyze if the market is validating the current bias or showing signs of a "Trap".

SIGNAL: {signal.get('symbol')} {signal.get('direction')} at {signal.get('entry_price')}
CURRENT_ROI: {signal.get('current_roi')}%
TIME_ELAPSED: {(signal.get('current_timestamp', 0) - signal.get('timestamp', 0)) / 60000:.1f} minutes

RECENT CANDLES (JSON):
{json.dumps(recent_candles[-5:], indent=2)}

INSTRUCTIONS:
1. Validating: Price moves in signal direction with conviction (Higher Highs for Long).
2. Warning: Price is flat or "leaning" against the bias (Dojis, long wicks opposing the direction).
3. Trap: Aggressive move against the entry level after a brief "fake" move in direction.

RESPOND IN JSON FORMAT ONLY:
{{
  "bias_health_score": 0.0-1.0, 
  "status": "VALIDATING" | "WEAKENING" | "TRAP_DETECTED",
  "reasoning": "concise description in Portuguese (PT-BR)",
  "suggested_action": "HOLD" | "EXIT_NOW" | "FLIP_IF_BREAKS",
  "flip_trigger_price": float or null
}}
"""
        try:
            response = llm_call_func(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "bias_health_score": 0.5,
                "status": "VALIDATING",
                "reasoning": f"Erro Scout: {str(e)}",
                "suggested_action": "HOLD",
                "flip_trigger_price": None
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            if "```" in response:
                response = response.split("```")[1].replace("json", "").strip()
            
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"bias_health_score": 0.5, "status": "VALIDATING", "reasoning": "Erro parse Scout", "suggested_action": "HOLD", "flip_trigger_price": None}
