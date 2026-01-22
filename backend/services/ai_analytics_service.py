# import pandas as pd # REMOVED to avoid heavy dependency and numpy conflicts
from typing import List, Dict
from datetime import datetime

class AIAnalyticsService:
    """Serviço para processar o histórico de sinais e gerar insights para a IA"""
    
    def __init__(self, db_manager):
        self.db = db_manager

    def get_market_correlations(self) -> Dict:
        """
        Analisa a correlação entre as features de mercado e o sucesso (Gain/Loss).
        Retorna estatísticas para o frontend. (Lightweight version without pandas)
        """
        history = self.db.get_signal_history(limit=500)
        
        if not history:
            return {"status": "NO_DATA", "message": "Sem dados históricos suficientes para análise. Continue operando!"}

        # Process data manually without pandas
        processed_data = []
        for sig in history:
            features = sig.get("ai_features", {})
            if not features: continue
            
            # Label processing
            status = sig.get("status")
            if status == "TP_HIT": label = 1
            elif status == "SL_HIT": label = 0
            else: continue
            
            row = {
                **features,
                "label": label,
                "symbol": sig.get("symbol", "N/A"),
                "signal_type": sig.get("signal_type", "UNKNOWN")
            }
            processed_data.append(row)
            
        if not processed_data:
            return {"status": "NO_LABELS", "message": "Dados coletados, aguardando finalização dos trades (Gain/Loss)."}

        # Calculate statistics manually
        total_samples = len(processed_data)
        wins = [d for d in processed_data if d["label"] == 1]
        losses = [d for d in processed_data if d["label"] == 0]
        
        win_rate = (len(wins) / total_samples * 100) if total_samples > 0 else 0
        
        # Helper to safely get mean
        def safe_mean(data, key):
            valid_vals = [d.get(key, 0) for d in data if d.get(key) is not None]
            return sum(valid_vals) / len(valid_vals) if valid_vals else 0

        stats = {
            "total_samples": total_samples,
            "win_rate": round(win_rate, 2),
            "avg_master_score_wins": round(safe_mean(wins, "master_score"), 2),
            "avg_master_score_losses": round(safe_mean(losses, "master_score"), 2),
        }
        
        # Correlation stats
        stats["oi_impact"] = {
            "avg_oi_change_wins": round(safe_mean(wins, "oi_change_pct"), 4),
            "avg_oi_change_losses": round(safe_mean(losses, "oi_change_pct"), 4)
        }
        
        # Performance by type
        type_stats = {}
        for d in processed_data:
            s_type = d.get("signal_type")
            if s_type not in type_stats:
                type_stats[s_type] = {"wins": 0, "count": 0}
            type_stats[s_type]["count"] += 1
            if d["label"] == 1:
                type_stats[s_type]["wins"] += 1
                
        stats["performance_by_type"] = {
            t: {
                "win_rate": round((v["wins"] / v["count"] * 100), 2) if v["count"] > 0 else 0,
                "count": v["count"]
            }
            for t, v in type_stats.items()
        }

        # Best Edge
        if type_stats:
            best_type = max(type_stats.items(), key=lambda item: (item[1]["wins"] / item[1]["count"] if item[1]["count"] > 0 else 0))
            best_type_name = best_type[0]
            best_win_rate = (best_type[1]["wins"] / best_type[1]["count"] * 100) if best_type[1]["count"] > 0 else 0
            
            stats["best_edge"] = {
                "type": best_type_name,
                "win_rate": round(best_win_rate, 2)
            }
        else:
             stats["best_edge"] = {"type": "N/A", "win_rate": 0}

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
