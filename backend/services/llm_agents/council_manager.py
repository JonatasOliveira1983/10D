from typing import Dict, Any, Callable
import json
from .risk_agent import RiskAgent
from .technical_agent import TechnicalAgent
from .fundamental_agent import FundamentalAgent
from .market_info_agent import MarketInfoAgent
from .ml_supervisor_agent import MLSupervisorAgent
from .bankroll_captain_agent import BankrollCaptainAgent

class CouncilManager:
    """
    The Coordinator.
    Manages the Multi-Agent Council.
    1. Runs individual agents (Risk, Technical, Fundamental, Market, ML).
    2. Aggregates their verdicts.
    3. Formats a 'Debate Prompt' for the LLM to synthesize the final decision.
    """
    
    def __init__(self, rag_memory=None):
        self.risk_agent = RiskAgent()
        self.technical_agent = TechnicalAgent(rag_memory=rag_memory)
        self.fundamental_agent = FundamentalAgent()
        self.market_agent = MarketInfoAgent()
        self.ml_supervisor = MLSupervisorAgent()
        self.bankroll_captain = BankrollCaptainAgent()
        self.agents = [
            self.risk_agent, 
            self.technical_agent, 
            self.fundamental_agent,
            self.market_agent,
            self.ml_supervisor,
            self.bankroll_captain
        ]

    def conduct_debate(self, signal: Dict[str, Any], market_context: Dict[str, Any], llm_call_func: Callable[[str], str]) -> Dict[str, Any]:
        """
        Run the full Council process.
        
        Args:
            signal: The signal data.
            market_context: The market environment data.
            llm_call_func: Function to call the LLM (takes prompt str, returns response str).
            
        Returns:
            Dict with final approval and Council details.
        """
        
        # 1. Run Individual Agents
        agent_outputs = {}
        for agent in self.agents:
            # Catch errors to prevent crash
            try:
                output = agent.analyze(signal, market_context)
                agent_outputs[agent.name] = output
            except Exception as e:
                agent_outputs[agent.name] = {
                    "score": 0, "verdict": "ERROR", "reasoning": str(e)
                }

        # 2. Construct Debate Prompt
        # Each agent speaks their mind
        debate_transcript = ""
        for name, out in agent_outputs.items():
            debate_transcript += f"### {name} ({out['verdict']} - Score: {out['score']})\n"
            debate_transcript += f"Opinion: {out['reasoning']}\n\n"
            
        # Add Learning Context if available in market_context (it's passed as a string sometimes, or we need to pass it)
        # Assuming market_context might have 'learning_context_str'
        
        prompt = f"""You are the High Judge of the Crypto Council.
Six specialized agents have debated a potential trade. Your job is to synthesize their opinions and make the FINAL DECISION.

SIGNAL: {signal.get('symbol')} {signal.get('direction')} | Entry: {signal.get('entry_price')} | Score: {signal.get('score')}

--- COUNCIL TRANSCRIPT ---
{debate_transcript}
--------------------------

INSTRUCTIONS:
1. REVIEW the agents' arguments.
2. DISSECT the 'Smart Money Hunger' (IHI 1-6 stars).
3. The RISK AGENT's veto ("REJECTED") is critical.
4. The ML SUPERVISOR protects against model performance decay.
5. The MARKET INFO AGENT provides context on new listing and news volatility.
6. The BANKROLL CAPTAIN ensures we don't exceed the 20% risk cap or the 10-slot capacity.
7. DECIDE if the trade proceeds or not.

RESPOND IN JSON FORMAT ONLY:
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Synthesize the debate. (Max 50 words)",
  "vote_breakdown": {{
     "technical": "{agent_outputs.get('Technical Agent', {}).get('verdict')}",
     "fundamental": "{agent_outputs.get('Fundamental Agent', {}).get('verdict')}",
     "risk": "{agent_outputs.get('Risk Agent', {}).get('verdict')}",
     "market": "{agent_outputs.get('market_info_agent', {}).get('verdict')}",
     "ml": "{agent_outputs.get('ml_supervisor_agent', {}).get('verdict')}",
     "bankroll": "{agent_outputs.get('bankroll_captain_agent', {}).get('verdict')}"
  }}
}}
"""

        # 3. Call LLM for Synthesis
        llm_response = llm_call_func(prompt)
        
        # 4. Handle Empty/Rate-Limited Response
        if llm_response is None:
            return {
                "approved": True, # Fallback to approval on technical failure
                "confidence": 0.5,
                "reasoning": "Council skipped (Rate Limit/Technical Issue)",
                "council_outputs": agent_outputs
            }
        
        # 5. Parse Response
        return self._parse_response(llm_response, agent_outputs)

    def _parse_response(self, response: str, agent_outputs: Dict) -> Dict:
        """Parse JSON response safely"""
        default_response = {
            "approved": True, # Default to True for non-blocking fallback
            "confidence": 0.5,
            "reasoning": "Council deadlock (Parsing Error)",
            "council_outputs": agent_outputs
        }
        
        if not response or not isinstance(response, str):
            return default_response

        try:
            # Clean generic markdown
            if "```" in response:
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1].replace("json", "").strip()
            
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                data["council_outputs"] = agent_outputs # Attach individual outputs
                return data
        except Exception:
            pass
            
        return default_response
