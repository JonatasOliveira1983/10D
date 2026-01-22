from services.database_manager import DatabaseManager
import json

def audit_signals():
    db = DatabaseManager()
    if not db.client:
        print("Erro: Supabase não conectado.")
        return

    print("--- Auditing Signal History ---")
    history = db.get_signal_history(limit=500)
    print(f"Total signals found in history: {len(history)}")

    samples_with_features = 0
    samples_without_features = 0
    status_counts = {}

    for sig in history:
        status = sig.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        features = sig.get("ai_features", {})
        if features:
            samples_with_features += 1
        else:
            samples_without_features += 1

    print(f"Signals with ai_features: {samples_with_features}")
    print(f"Signals without ai_features: {samples_without_features}")
    print(f"Status breakdown: {status_counts}")

    if history:
        print("\nLast signal sample:")
        print(json.dumps(history[0], indent=2))

if __name__ == "__main__":
    audit_signals()
