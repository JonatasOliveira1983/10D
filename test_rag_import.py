import sys
import os
import time

# UTF-8 fix for Windows
import io
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("STEP 1: Importing RAGMemory...", flush=True)
try:
    start = time.time()
    from backend.services.rag_memory import RAGMemory
    print(f"✅ STEP 1 OK in {time.time() - start:.2f}s", flush=True)
except Exception as e:
    print(f"❌ STEP 1 FAILED: {e}", flush=True)
    sys.exit(1)

print("STEP 2: Initializing RAGMemory...", flush=True)
try:
    start = time.time()
    # Use relative path if running from root
    memory = RAGMemory(storage_path="backend/data/memory_index.json")
    print(f"✅ STEP 2 OK in {time.time() - start:.2f}s", flush=True)
    print(f"Memory size: {len(memory.vectors)}", flush=True)
except Exception as e:
    print(f"❌ STEP 2 FAILED: {e}", flush=True)

print("ALL STEPS COMPLETED", flush=True)
