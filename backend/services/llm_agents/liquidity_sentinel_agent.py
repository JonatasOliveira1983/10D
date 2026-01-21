import json
from typing import Dict, Any

class LiquiditySentinelAgent:
    """
    The Sentinel.
    Analyzes Order Flow data (OI, CVD, LSR, Absorption) to detect institutional manipulation.
    If it detects that a move in one direction is being absorbed by large limit orders 
    in the opposite direction, it flags a "High Liquidity Trap".
    """
    
    def __init__(self):
        self.name = "Liquidity Sentinel"

    def analyze_order_flow(self, signal: Dict[str, Any], flow_data: Dict[str, Any], llm_call_func: Any) -> Dict[str, Any]:
        """
        Analyzes real-time order flow data to confirm if the move is "Real" or "Induced".
        """
        
        prompt = f"""You are the Sentinel specializing in Institutional Order Flow.
Analyze if Big Players are absorbing retail liquidity or following the trend.

DATA:
Symbol: {signal.get('symbol')}
Direction: {signal.get('direction')}
OI Change: {flow_data.get('oi_change_pct')}% (High positive often indicates new positions)
CVD Delta: {flow_data.get('cvd_delta')} (Negative while price rises = Absorption/Selling into strength)
LS Ratio: {flow_data.get('lsr_latest')} (High retail long = Good for whales to hunt Short)

INSTRUCTIONS:
1. DETECT if there is "Institutional Absorption" (price moves one way, but CVD/OI shows big players moving opposite).
2. IDENTIFY if we are in an "Inducement Phase" (manipulation to trigger retail SL).
3. ASSESS the risk of a sharp reversal (Flip).

RESPOND IN JSON FORMAT ONLY:
{{
  "liquidity_conviction": 0.0-1.0, 
  "flow_status": "CONFLUENT" | "ABSORPTION" | "MANIPULATION",
  "reasoning": "concise description in Portuguese (PT-BR)",
  "trap_probability": 0.0-1.0,
  "action": "PROCEED" | "CAUTION" | "ABORT_AND_FLIP"
}}
"""
        try:
            response = llm_call_func(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "liquidity_conviction": 0.5,
                "flow_status": "CONFLUENT",
                "reasoning": f"Erro Sentinel: {str(e)}",
                "trap_probability": 0.2,
                "action": "PROCEED"
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
        return {"liquidity_conviction": 0.5, "flow_status": "CONFLUENT", "reasoning": "Erro parse Sentinel", "trap_probability": 0.2, "action": "PROCEED"}
