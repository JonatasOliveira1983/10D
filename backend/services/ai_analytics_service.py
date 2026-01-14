import pandas as pd
from typing import List, Dict
from datetime import datetime

class AIAnalyticsService:
    """Serviço para processar o histórico de sinais e gerar insights para a IA"""
    
    def __init__(self, db_manager):
        self.db = db_manager

    def get_market_correlations(self) -> Dict:
        """
        Analisa a correlação entre as features de mercado e o sucesso (Gain/Loss).
        Retorna estatísticas para o frontend.
        """
        history = self.db.get_signal_history(limit=500)
        
        if not history:
            return {"status": "NO_DATA", "message": "Sem dados históricos suficientes para análise. Continue operando!"}

        # Converter para DataFrame para facilitar análise
        df_list = []
        for sig in history:
            features = sig.get("ai_features", {})
            if not features: continue
            
            # Label: 1 para Gain (TP_HIT), 0 para Loss (SL_HIT), ignore outros status (EXPIRED)
            status = sig.get("status")
            if status == "TP_HIT": label = 1
            elif status == "SL_HIT": label = 0
            else: continue
            
            row = {
                **features,
                "label": label,
                "symbol": sig.get("symbol"),
                "signal_type": sig.get("signal_type")
            }
            df_list.append(row)
            
        if not df_list:
            return {"status": "NO_LABELS", "message": "Dados coletados, aguardando finalização dos trades (Gain/Loss)."}

        df = pd.DataFrame(df_list)
        
        # Estatísticas Básicas
        stats = {
            "total_samples": len(df),
            "win_rate": round(df["label"].mean() * 100, 2),
            "avg_master_score_wins": round(df[df["label"] == 1]["master_score"].mean(), 2),
            "avg_master_score_losses": round(df[df["label"] == 0]["master_score"].mean(), 2),
        }
        
        # Correlação com OI e LSR (Exemplo simples)
        # Sinais onde OI subiu e deu Gain vs OI subiu e deu Loss
        stats["oi_impact"] = {
            "avg_oi_change_wins": round(df[df["label"] == 1]["oi_change_pct"].mean(), 4),
            "avg_oi_change_losses": round(df[df["label"] == 0]["oi_change_pct"].mean(), 4)
        }
        
        # Desempenho por tipo de sinal
        type_perf = df.groupby("signal_type")["label"].agg(['mean', 'count']).to_dict('index')
        stats["performance_by_type"] = {
            t: {"win_rate": round(v['mean'] * 100, 2), "count": v['count']} 
            for t, v in type_perf.items()
        }

        # Sugestão de "Vantagem Estatística" (Heurística simples)
        highest_win_rate_type = max(type_perf, key=lambda k: type_perf[k]['mean'])
        stats["best_edge"] = {
            "type": highest_win_rate_type,
            "win_rate": round(type_perf[highest_win_rate_type]['mean'] * 100, 2)
        }

        return {"status": "READY", "data": stats}

    def get_training_progress(self) -> Dict:
        """Dashboard de progresso da coleta de dados"""
        history = self.db.get_signal_history(limit=1000)
        labeled_count = sum(1 for s in history if s.get("status") in ["TP_HIT", "SL_HIT", "EXPIRED"])
        
        target = 300 # Meta para treinamento robusto
        progress = (labeled_count / target) * 100 if labeled_count < target else 100
        
        return {
            "current_samples": labeled_count,
            "target_samples": target,
            "progress_pct": round(progress, 2),
            "is_ready_to_train": labeled_count >= target
        }

    def prepare_training_data(self) -> List[Dict]:
        """
        Prepara o histórico completo do Supabase para exportação para a M.E (Aprendizado de Máquina).
        """
        history = self.db.get_signal_history(limit=1000)
        training_set = []
        
        for sig in history:
            features = sig.get("ai_features")
            status = sig.get("status")
            
            if not features or not status:
                continue
                
            # Codificação do Label para ML
            # Gain = 1, Loss = 0, Expired = 0.5 (ou ignorar se quiser apenas extremos)
            label = -1
            if status == "TP_HIT": label = 1
            elif status == "SL_HIT": label = 0
            elif status == "EXPIRED": label = 0.5
            
            training_set.append({
                "signal_id": sig.get("id"),
                "symbol": sig.get("symbol"),
                "timestamp": sig.get("timestamp"),
                "label": label,
                **features
            })
            
        return training_set
