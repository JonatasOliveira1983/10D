from services.database_manager import DatabaseManager
import json

def inspect():
    db = DatabaseManager()
    if not db.client: return
    history = db.get_signal_history(limit=5)
    for i, sig in enumerate(history):
        print(f"\n--- Signal {i+1} ---")
        print(f"ID: {sig.get('id')}")
        print(f"Status: {sig.get('status')}")
        print(f"Has AI Features: {'ai_features' in sig}")
        if 'ai_features' in sig:
            print(f"Features: {json.dumps(sig['ai_features'], indent=2)}")

if __name__ == "__main__":
    inspect()
