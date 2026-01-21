import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import json
from services.llm_agents.adaptive_bias_agent import AdaptiveBiasAgent
from services.llm_agents.liquidity_sentinel_agent import LiquiditySentinelAgent

def test_agents_direct():
    print("Testing Scout and Sentinel Directly...")
    
    scout = AdaptiveBiasAgent()
    sentinel = LiquiditySentinelAgent()
    
    # Mock LLM func
    def mock_llm(p):
        if "Scout" in p:
            return json.dumps({
                "bias_health_score": 0.1,
                "status": "TRAP_DETECTED",
                "reasoning": "Price rejection after fake out.",
                "suggested_action": "EXIT_NOW",
                "flip_trigger_price": 0.99
            })
        return json.dumps({
            "liquidity_conviction": 0.2,
            "flow_status": "ABSORPTION",
            "reasoning": "Large sell walls detected.",
            "trap_probability": 0.85,
            "action": "ABORT_AND_FLIP"
        })

    signal = {"symbol": "BTC", "direction": "LONG", "entry_price": 50000, "timestamp": 123456}
    candles = [{"close": 50100}, {"close": 49900}]
    flow = {"oi_change_pct": 5, "cvd_delta": -100}
    
    scout_res = scout.analyze_reaction(signal, candles, mock_llm)
    sentinel_res = sentinel.analyze_order_flow(signal, flow, mock_llm)
    
    print("Scout Result:", scout_res["status"])
    print("Sentinel Result:", sentinel_res["flow_status"])
    
    assert scout_res["status"] == "TRAP_DETECTED"
    assert sentinel_res["action"] == "ABORT_AND_FLIP"
    print("✅ Agents Logic Verified!")

if __name__ == "__main__":
    test_agents_direct()
