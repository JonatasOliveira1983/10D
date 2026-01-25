import json
from typing import Dict, Any, List

class PortfolioGovernorAgent:
    """
    The Governor.
    Manages portfolio-wide risk by checking correlations and exposure.
    Prevents the system from opening too many trades in the same direction or sector.
    """
    
    def __init__(self):
        self.name = "Portfolio Governor"

    def authorize_trade(self, candidate_signal: Dict[str, Any], active_signals: List[Dict], llm_call_func: Any) -> Dict[str, Any]:
        """
        Determines if a new trade should be opened based on existing portfolio exposure.
        """
        
        exposure_summary = {
            "total_active": len(active_signals),
            "long_count": sum(1 for s in active_signals if s.get("direction") == "LONG"),
            "short_count": sum(1 for s in active_signals if s.get("direction") == "SHORT"),
            "assets": [s.get("symbol") for s in active_signals]
        }

        prompt = f"""You are the Portfolio Governor. Your job is to prevent "Correlation Overload".
A new signal has been generated, but you must decide if it's safe to add to the current portfolio.

NEW SIGNAL: {candidate_signal.get('symbol')} {candidate_signal.get('direction')}
CURRENT PORTFOLIO: {json.dumps(exposure_summary)}

RULES:
1. MAX EXPOSURE: Do not allow more than 10 active trades.
2. CORRELATION: If we already have 5 LONGs in Alts, be cautious but allow up to 10 total if quality is high.
3. CONVICTION: Only allow the trade if it doesn't create a "One-Way Bettor" scenario.

RESPOND IN JSON FORMAT ONLY. ALL TEXT FIELDS MUST BE IN PORTUGUESE (PT-BR):
{{
  "authorized": bool,
  "risk_score": 0-100,
  "reasoning": "Portuguese (PT-BR) explanation",
  "suggested_size_reduction": 0.0-1.0
}}
"""
        try:
            response = llm_call_func(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {"authorized": True, "risk_score": 50, "reasoning": f"Erro Governor: {str(e)}", "suggested_size_reduction": 0}

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
        return {"authorized": True, "risk_score": 50, "reasoning": "Erro parse Governor", "suggested_size_reduction": 0}
