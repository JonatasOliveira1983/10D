"""
Script para treinar o modelo ML do sistema 10D
Execute este script quando tiver pelo menos 50-100 sinais finalizados no banco
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ml_predictor import MLPredictor
from services.database_manager import DatabaseManager
from config import (
    ML_MODEL_PATH, ML_METRICS_PATH, ML_MIN_SAMPLES, ML_AUTO_RETRAIN_INTERVAL
)

def main():
    print("="*80)
    print(" TREINAMENTO DO MODELO ML - SISTEMA 10D")
    print("="*80)
    print()
    
    # Initialize database and ML predictor
    print("[1/4] Conectando ao banco de dados...")
    db = DatabaseManager()
    
    ml_config = {
        "ML_MODEL_PATH": ML_MODEL_PATH,
        "ML_METRICS_PATH": ML_METRICS_PATH,
        "ML_MIN_SAMPLES": ML_MIN_SAMPLES,
        "ML_AUTO_RETRAIN_INTERVAL": ML_AUTO_RETRAIN_INTERVAL
    }
    
    print("[2/4] Inicializando ML Predictor...")
    predictor = MLPredictor(db, ml_config)
    
    # Check available samples
    print("[3/4] Verificando sinais disponiveis...")
    signals = db.get_signals_with_features(limit=1000)
    labeled_signals = [s for s in signals if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"]]
    
    print(f"\n Estatisticas:")
    print(f"  - Total de sinais com features: {len(signals)}")
    print(f"  - Sinais finalizados (TP/SL/EXPIRED): {len(labeled_signals)}")
    print(f"  - Minimo necessario: {ML_MIN_SAMPLES}")
    print()
    
    if len(labeled_signals) < ML_MIN_SAMPLES:
        print(f" AVISO: Voce tem apenas {len(labeled_signals)} sinais finalizados.")
        print(f"   Recomendado: pelo menos {ML_MIN_SAMPLES} sinais.")
        print("FORCE MODE: Auto-approving training...")
        
        # Use lower threshold
        min_samples = max(2, len(labeled_signals))
    else:
        min_samples = ML_MIN_SAMPLES
    
    # Train model
    print(f"\n[4/4] Treinando modelo com {len(labeled_signals)} sinais...")
    print(" Isso pode levar alguns segundos...\n")
    
    try:
        metrics = predictor.train_model(min_samples=min_samples)
        
        if metrics.get("status") == "SUCCESS":
            print("\n" + "="*80)
            print(" MODELO TREINADO COM SUCESSO!")
            print("="*80)
            print(f"\n Metricas do Modelo:")
            print(f"  - Acuracia: {metrics['metrics']['accuracy']:.2%}")
            print(f"  - Precisao: {metrics['metrics']['precision']:.2%}")
            print(f"  - Recall: {metrics['metrics']['recall']:.2%}")
            print(f"  - F1-Score: {metrics['metrics']['f1_score']:.2%}")
            print(f"\n Dados de Treinamento:")
            print(f"  - Total de amostras: {metrics['samples']['total']}")
            print(f"  - Treino: {metrics['samples']['train']}")
            print(f"  - Teste: {metrics['samples']['test']}")
            print(f"  - Ganhos (TP): {metrics['samples']['wins']}")
            print(f"  - Perdas (SL/EXPIRED): {metrics['samples']['losses']}")
            print(f"\n Top 3 Features Importantes:")
            for i, (feature, importance) in enumerate(list(metrics['feature_importance'].items())[:3], 1):
                print(f"  {i}. {feature}: {importance:.4f}")
            print("\n" + "="*80)
            print(" Agora voce pode reiniciar o backend para usar o modelo treinado!")
            print("="*80)
        else:
            print("\n Falha no treinamento:")
            print(f"   {metrics.get('message', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"\n ERRO durante o treinamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
