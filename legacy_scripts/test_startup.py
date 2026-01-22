import sys
import os
import time

# Add backend to path
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

print(f"Testing import from: {backend_dir}")

try:
    print("Importing SignalGenerator...")
    from services.signal_generator import SignalGenerator
    
    print("Creating SignalGenerator instance...")
    start_time = time.time()
    # Mocking config constants if needed, but they should be in config.py
    
    sig = SignalGenerator()
    end_time = time.time()
    
    print(f"SignalGenerator created in {end_time - start_time:.2f}s")
    
    # Check RAG injection
    print(f"RAG Memory initialized: {sig.rag_memory is not None}")
    
    # Check LLM RAG injection
    if sig.llm_brain:
        print(f"LLM Brain initialized: {sig.llm_brain is not None}")
        print(f"LLM Brain has RAG: {sig.llm_brain.rag_memory is not None}")
        print(f"Council has RAG: {sig.llm_brain.council.technical_agent.memory == sig.rag_memory}")
    else:
        print("LLM Brain disabled (expected if no API key)")

    print(f"System Ready Flag: {sig.system_ready}")
    print("SUCCESS: Syntax and basic initialization check passed.")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
