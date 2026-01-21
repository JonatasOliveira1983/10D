import json
from typing import Dict, Any

class GlobalAnchorAgent:
    """
    The Global Anchor.
    Monitors Macro indicators like DXY, S&P 500, and overall Crypto dominance.
    Sets the "Global Confidence" level for the entire system.
    """
    
    def __init__(self):
        self.name = "Global Anchor"

    def analyze_macro_context(self, macro_data: Dict[str, Any], llm_call_func: Any) -> Dict[str, Any]:
        """
        Analyzes the global financial environment to determine its impact on Crypto.
        """
        
        prompt = f"""You are the Global Macro Anchor.
Assess the impact of the current traditional financial environment on the Crypto market.

MACRO DATA:
{json.dumps(macro_data, indent=2)}

INSTRUCTIONS:
1. Bullish Anchor: DXY down, S&P up, BTC Dominance stable.
2. Bearish Anchor: DXY spiking, Fear index high, Liquidity draining.
3. Determine a 'Global Confidence Factor' (0.5 to 1.5) which will multiply all signal scores.

RESPOND IN JSON FORMAT ONLY. ALL TEXT FIELDS MUST BE IN PORTUGUESE (PT-BR):
{{
  "global_sentiment": "BULLISH" | "NEUTRAL" | "BEARISH",
  "confidence_multiplier": float,
  "macro_risk_level": "LOW" | "MODERATE" | "HIGH",
  "summary": "Portuguese (PT-BR) summary of global status",
  "key_warning": "Any specific macro alert"
}}
"""
        try:
            response = llm_call_func(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "global_sentiment": "NEUTRAL",
                "confidence_multiplier": 1.0,
                "macro_risk_level": "MODERATE",
                "summary": f"Erro Macro: {str(e)}",
                "key_warning": "N/A"
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
        return {"global_sentiment": "NEUTRAL", "confidence_multiplier": 1.0, "macro_risk_level": "MODERATE"}
