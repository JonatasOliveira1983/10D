from typing import Dict, Any, Callable
import json
from .risk_agent import RiskAgent
from .technical_agent import TechnicalAgent
from .fundamental_agent import FundamentalAgent

class CouncilManager:
    """
    The Coordinator.
    Manages the Multi-Agent Council.
    1. Runs individual agents (Risk, Technical, Fundamental).
    2. Aggregates their verdicts.
    3. Formats a 'Debate Prompt' for the LLM to synthesize the final decision.
    """
    
    def __init__(self, rag_memory=None):
        self.risk_agent = RiskAgent()
        self.technical_agent = TechnicalAgent(rag_memory=rag_memory)
        self.fundamental_agent = FundamentalAgent()
        self.agents = [self.risk_agent, self.technical_agent, self.fundamental_agent]

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
Three specialized agents have debated a potential trade. Your job is to synthesize their opinions and make the FINAL DECISION.

SIGNAL: {signal.get('symbol')} {signal.get('direction')} | Entry: {signal.get('entry_price')} | Score: {signal.get('score')}

--- COUNCIL TRANSCRIPT ---
{debate_transcript}
--------------------------

INSTRUCTIONS:
1. REVIEW the agents' arguments.
2. The RISK AGENT's veto ("REJECTED") should be taken very seriously.
3. The FUNDAMENTAL AGENT (Sentinel) protects against market crashes.
4. DECIDE if the trade proceeds or not.

RESPOND IN JSON FORMAT ONLY:
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Synthesize the debate. Why did you reach this verdict? (Max 50 words)",
  "vote_breakdown": {{
     "technical": "{agent_outputs['Technical Agent']['verdict']}",
     "fundamental": "{agent_outputs['Fundamental Agent']['verdict']}",
     "risk": "{agent_outputs['Risk Agent']['verdict']}"
  }}
}}
"""

        # 3. Call LLM for Synthesis
        llm_response = llm_call_func(prompt)
        
        # 4. Parse Response
        return self._parse_response(llm_response, agent_outputs)

    def _parse_response(self, response: str, agent_outputs: Dict) -> Dict:
        """Parse JSON response safely"""
        default_response = {
            "approved": False,
            "confidence": 0.0,
            "reasoning": "Council deadlock (Parsing Error)",
            "council_outputs": agent_outputs
        }
        
        if not response:
            return default_response

        try:
            # Clean generic markdown
            if "```" in response:
                response = response.split("```")[1].replace("json", "").strip()
            
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
