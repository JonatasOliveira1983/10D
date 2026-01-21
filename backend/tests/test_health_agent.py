import sys
import os
import json
import time

# Mocking a minimal environment to test the agent logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_agents.system_health_agent import SystemHealthAgent

def mock_llm_call(prompt):
    print("\n--- LLM PROMPT ---")
    print(prompt[:200] + "...")
    print("------------------\n")
    
    # Return a simulated healthy response
    return """
    {
      "health_score": 95,
      "status": "HEALTHY",
      "summary": "O sistema está operando com ótimos parâmetros de CPU e memória. Conexão com banco estável.",
      "issues": [],
      "recommendations": ["Aumentar intervalo de busca se a latência subir"]
    }
    """

def test_agent_healthy():
    print("Testing Agent with Healthy Vitals...")
    agent = SystemHealthAgent()
    vitals = {
        "system": {"cpu_usage": 10.5, "memory_usage": 45.0},
        "components": {"database": "STABLE", "bybit_api": 150}
    }
    result = agent.analyze_vitals(vitals, mock_llm_call)
    print("RESULT:", json.dumps(result, indent=2))
    assert result["health_score"] >= 90
    assert result["status"] == "HEALTHY"

def test_agent_critical():
    print("\nTesting Agent with Critical Vitals...")
    agent = SystemHealthAgent()
    vitals = {
        "system": {"cpu_usage": 99.0, "memory_usage": 98.0},
        "components": {"database": "DISCONNECTED", "bybit_api": -1}
    }
    
    def mock_critical_call(prompt):
        return """
        {
          "health_score": 10,
          "status": "CRITICAL",
          "summary": "Falha crítica detectada. CPU saturada e banco de dados desconectado.",
          "issues": ["HIGH_CPU", "DB_DISCONNECTED"],
          "recommendations": ["Reiniciar servidor", "Verificar conexão Supabase"]
        }
        """

    result = agent.analyze_vitals(vitals, mock_critical_call)
    print("RESULT:", json.dumps(result, indent=2))
    assert result["health_score"] <= 20
    assert result["status"] == "CRITICAL"

if __name__ == "__main__":
    try:
        test_agent_healthy()
        test_agent_critical()
        print("\n✅ Verification tests passed!")
    except Exception as e:
        print(f"\n❌ Verification tests failed: {e}")
        sys.exit(1)
