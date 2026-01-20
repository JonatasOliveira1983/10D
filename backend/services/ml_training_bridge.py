import pandas as pd
import json
from datetime import datetime
import sys
import os

# Ajuste de path para execução direta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_manager import DatabaseManager
from services.ai_analytics_service import AIAnalyticsService

class MLTrainingBridge:
    """
    Ponte entre o banco de dados e o sistema de Aprendizado de Máquina.
    Responsável por coletar dados, simular o aprendizado e gerar o 'Brain' (insights) do sistema.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.analytics = AIAnalyticsService(self.db)
        self.brain_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_brain.json")

    def run_cycle(self):
        print(f"[{datetime.now()}] Iniciando ciclo de treinamento ML...", flush=True)
        
        # 1. Coletar dados preparados
        data = self.analytics.prepare_training_data()
        if len(data) < 10:
            print("Dados insuficientes para rodar o ciclo de ML.", flush=True)
            return
            
        df = pd.DataFrame(data)
        
        # 2. Gerar Insights (Simulação de Pesos de Modelo)
        # O objetivo aqui é identificar quais features estão mais correlacionadas com o Gain (label=1)
        insights = {
            "last_training": datetime.now().isoformat(),
            "samples_analyzed": len(df),
            "feature_importance": {},
            "optimal_thresholds": {}
        }
        
        # Correlação simples para identificar pesos das features
        numeric_df = df.drop(columns=["signal_id", "symbol", "timestamp"])
        correlations = numeric_df.corr()["label"].drop("label").to_dict()
        
        # Formatar importância baseada na correlação absoluta
        for feat, corr in correlations.items():
            insights["feature_importance"][feat] = round(abs(corr), 4)
            
        # Sugestão de Threshold (Exemplo: Master Score ideal baseado em vitórias)
        wins = df[df["label"] == 1]
        if not wins.empty:
            insights["optimal_thresholds"]["min_master_score"] = round(wins["master_score"].mean(), 2)
            insights["optimal_thresholds"]["optimal_rsi_range"] = [
                round(wins["rsi_value"].min(), 1),
                round(wins["rsi_value"].max(), 1)
            ]
            
        # 3. Salvar o 'Brain' para uso do Scorer
        with open(self.brain_path, "w") as f:
            json.dump(insights, f, indent=4)
            
        print(f"Ciclo ML concluido. Insights salvos em: {self.brain_path}", flush=True)
        return insights

if __name__ == "__main__":
    bridge = MLTrainingBridge()
    bridge.run_cycle()
