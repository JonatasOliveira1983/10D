import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


with open("import_log.txt", "w", encoding="utf-8") as f:
    try:
        f.write("Attempting to import CouncilManager...\n")
        from services.llm_agents.council_manager import CouncilManager
        f.write("✅ CouncilManager imported successfully!\n")
        
        f.write("Attempting to import LLMTradingBrain...\n")
        from services.llm_trading_brain import LLMTradingBrain
        f.write("✅ LLMTradingBrain imported successfully!\n")
        
    except Exception as e:
        f.write(f"❌ IMPORT ERROR: {e}\n")
        import traceback
        traceback.print_exc(file=f)

