import json
from typing import Dict, Any, List

class StrategistAgent:
    """
    The Strategist.
    Analyzes historical data and failed signals to identify patterns.
    Provides long-term optimization rules for other agents.
    """
    
    def __init__(self):
        self.name = "Global Strategist"
        self.optimization_rules = {}

    def analyze_performance(self, trade_history: List[Dict], llm_call_func: Any) -> Dict[str, Any]:
        """
        Analyzes a batch of recent trades to find common failure or success patterns.
        """
        
        # Prepare a summary of recent trades for the LLM
        history_summary = []
        for trade in trade_history[-10:]: # Look at last 10
            history_summary.append({
                "symbol": trade.get("symbol"),
                "direction": trade.get("direction"),
                "status": trade.get("status"),
                "roi": trade.get("final_roi"),
                "score": trade.get("score"),
                "reasoning": trade.get("llm_validation", {}).get("reasoning", "")[:100]
            })

        prompt = f"""You are the Multi-Agent Strategist for the 10D System.
Your goal is to learn from past performance and optimize system logic.

RECENT TRADE HISTORY (JSON):
{json.dumps(history_summary, indent=2)}

INSTRUCTIONS:
1. Identify if specific symbols or market conditions are causing repeated losses.
2. Provide actionable "Optimization Rules" for:
   - Increasing score requirements for certain coins.
   - Adjusting sensitivity of the Sentinel/Scout agents.
   - Identifying market regimes where the system is failing.

RESPOND IN JSON FORMAT ONLY. ALL TEXT FIELDS MUST BE IN PORTUGUESE (PT-BR):
{{
  "performance_grade": "A" | "B" | "C" | "D" | "F",
  "key_findings": ["point 1", "point 2"],
  "optimization_rules": {{
      "restrict_symbols": [],
      "min_score_adjustment": 0,
      "sentinel_sensitivity": "normal" | "high" | "strict"
  }},
  "advice": "Portuguese (PT-BR) advice for the trader"
}}
"""
        try:
            response = llm_call_func(prompt)
            result = self._parse_response(response)
            if result:
                self.optimization_rules = result.get("optimization_rules", {})
            return result
        except Exception as e:
            return {"error": str(e), "advice": "Mantenha a cautela."}

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
        return {}
