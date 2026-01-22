import sys
import os
import time

print("STEP 1: Importing google.generativeai...", flush=True)
try:
    import google.generativeai as genai
    print("✅ STEP 1 OK", flush=True)
except Exception as e:
    print(f"❌ STEP 1 FAILED: {e}", flush=True)
    sys.exit(1)

print("STEP 2: Configuring GEMINI_API_KEY...", flush=True)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Try loading from .env
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ STEP 2 FAILED: GEMINI_API_KEY not found", flush=True)
else:
    try:
        genai.configure(api_key=api_key)
        print("✅ STEP 2 OK", flush=True)
    except Exception as e:
        print(f"❌ STEP 2 FAILED: {e}", flush=True)

print("STEP 3: Initializing model...", flush=True)
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅ STEP 3 OK", flush=True)
except Exception as e:
    print(f"❌ STEP 3 FAILED: {e}", flush=True)

print("STEP 4: Test generation...", flush=True)
try:
    start = time.time()
    response = model.generate_content("ping", generation_config=genai.types.GenerationConfig(max_output_tokens=10))
    print(f"✅ STEP 4 OK: '{response.text.strip()}' in {time.time() - start:.2f}s", flush=True)
except Exception as e:
    print(f"❌ STEP 4 FAILED: {e}", flush=True)

print("ALL STEPS COMPLETED", flush=True)
