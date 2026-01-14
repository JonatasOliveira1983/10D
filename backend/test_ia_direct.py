from services.database_manager import DatabaseManager
from services.ai_analytics_service import AIAnalyticsService
import os

def test_ia_data():
    print("Iniciando teste de dados IA...", flush=True)
    db = DatabaseManager()
    if not db.client:
        print("Erro: Cliente Supabase não inicializado!", flush=True)
        return
        
    analytics = AIAnalyticsService(db)
    
    print("\n[1] Testando Progress...", flush=True)
    progress = analytics.get_training_progress()
    print(f"Progress: {progress}", flush=True)
    
    print("\n[2] Testando Correlations...", flush=True)
    correlations = analytics.get_market_correlations()
    print(f"Correlations Status: {correlations.get('status')}", flush=True)
    if correlations.get('status') == 'READY':
        print(f"Win Rate: {correlations['data']['win_rate']}%", flush=True)
    else:
        print(f"Message: {correlations.get('message')}", flush=True)

if __name__ == "__main__":
    test_ia_data()
