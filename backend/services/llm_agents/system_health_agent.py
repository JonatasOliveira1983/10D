import json
from datetime import datetime
from typing import Dict, Any, Optional

class SystemHealthAgent:
    """
    Agent responsible for monitoring system "vitals" and providing AI-based diagnostics.
    It analyzes database connectivity, API latencies, and scanner status to predict
    or diagnose system failures.
    """

    def __init__(self, llm_id: str = "gemini-1.5-flash"):
        self.name = "System Health Agent"
        self.llm_id = llm_id

    def analyze_vitals(self, vitals: Dict[str, Any], llm_call_func: Any) -> Dict[str, Any]:
        """
        Takes system vitals and returns an AI health assessment.
        """
        
        prompt = f"""You are the System Guardian for the 10D Trading System.
Review the following SYSTEM VITALS and provide a health assessment.

VITALS:
{json.dumps(vitals, indent=2)}

INSTRUCTIONS:
1. Identify any critical issues (e.g., DB disconnected, high API latency, scanner stuck).
2. Provide a "Health Score" (0-100).
3. Suggest "Self-Healing" actions if scores are low.
4. Keep the summary concise (max 50 words).

RESPOND IN JSON FORMAT ONLY:
{{
  "health_score": int,
  "status": "HEALTHY" | "DEGRADED" | "CRITICAL",
  "summary": "concise description in Portuguese (PT-BR)",
  "issues": [string],
  "recommendations": [string]
}}
"""
        try:
            response = llm_call_func(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "health_score": 50,
                "status": "DEGRADED",
                "summary": f"Erro na análise de IA: {str(e)}",
                "issues": ["IA_OFFLINE"],
                "recommendations": ["Verificar chave de API do Gemini"]
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Safely parse the JSON response from the LLM"""
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
                return json.loads(json_str)
        except:
            pass
            
        return {
            "health_score": 0,
            "status": "CRITICAL",
            "summary": "Falha crítica ao processar diagnóstico de IA.",
            "issues": ["PARSING_ERROR"],
            "recommendations": ["Reiniciar monitor de saúde"]
        }
