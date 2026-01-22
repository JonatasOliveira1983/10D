import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.rag_memory import RAGMemory
from services.llm_agents.technical_agent import TechnicalAgent

def test_rag_integration():
    print("="*60)
    print("🧠 TESTING RAG MEMORY INTEGRATION")
    print("="*60)
    
    # 1. Test Memory Direct
    print("\n[1] Testing Vector Search...")
    memory = RAGMemory(storage_path="backend/data/memory_index.json")
    if not memory.vectors:
        print("❌ Memory is empty! Run build_memory.py first.")
        return
        
    mock_signal = {
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "score": 80,
        "volume_ratio": 2.0,
        "indicators": {"rsi": 45}
    }
    
    matches = memory.find_similar(mock_signal, k=3)
    print(f"✅ Found {len(matches)} similar patterns.")
    for i, m in enumerate(matches):
        print(f"   {i+1}. Sim: {m['similarity']:.4f} | Outcome: {m['metadata']['outcome']['status']} ROI: {m['metadata']['outcome']['roi']}%")

    # 2. Test Agent Integration
    print("\n[2] Testing Technical Agent with Memory...")
    agent = TechnicalAgent()
    # Force memory path to be correct for test execution context if needed
    agent.memory = memory 
    
    context = {"btc_regime": "TRENDING", "decoupling_score": 0.5}
    
    result = agent.analyze(mock_signal, context)
    
    print(f"Verdict: {result['verdict']} (Score: {result['score']})")
    print("Reasoning:")
    has_rag_mention = False
    for r in result['reasoning']:
        print(f" - {r}")
        if "Historical Pattern" in r:
            has_rag_mention = True
            
    if has_rag_mention:
        print("\n✅ SUCCESS: Agent used historical memory in reasoning!")
    else:
        print("\n⚠️ WARNING: Agent did NOT mention historical memory.")


if __name__ == "__main__":
    with open("test_rag_log.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        test_rag_integration()

