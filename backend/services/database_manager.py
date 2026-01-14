import os
import json
import time
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

class DatabaseManager:
    """Gerenciador de conexão e operações com Supabase (PostgreSQL)"""
    
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            print("[DB ERROR] SUPABASE_URL ou SUPABASE_ANON_KEY não encontradas no .env", flush=True)
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                print("[DB] Conexão com Supabase estabelecida", flush=True)
            except Exception as e:
                print(f"[DB ERROR] Falha ao conectar ao Supabase: {e}", flush=True)
                self.client = None

    # --- Métodos para Sinais ---

    def save_signal(self, signal: Dict):
        """Salva ou atualiza um sinal no banco"""
        if not self.client: return
        
        try:
            # Prepara o payload simplificado para colunas e o completo para JSONB
            data = {
                "id": signal["id"],
                "symbol": signal["symbol"],
                "direction": signal["direction"],
                "signal_type": signal.get("signal_type"),
                "entry_price": signal.get("entry_price"),
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit"),
                "score": signal.get("score"),
                "status": signal.get("status", "ACTIVE"),
                "final_roi": signal.get("final_roi"),
                "timestamp": signal.get("timestamp"),
                "exit_timestamp": signal.get("exit_timestamp"),
                "payload": signal # Objeto completo
            }
            
            self.client.table("signals").upsert(data).execute()
        except Exception as e:
            print(f"[DB ERROR] Erro ao salvar sinal {signal.get('symbol')}: {e}", flush=True)

    def get_active_signals(self) -> Dict[str, Dict]:
        """Recupera todos os sinais com status ACTIVE"""
        if not self.client: return {}
        
        try:
            response = self.client.table("signals").select("*").eq("status", "ACTIVE").execute()
            signals = {}
            for row in response.data:
                # Usamos o payload completo salvo no JSONB, ou fallback para dados da raiz
                sig_data = row.get("payload") or row
                if sig_data and "symbol" in sig_data:
                    signals[row["symbol"]] = sig_data
            return signals
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar sinais ativos: {e}", flush=True)
            return {}

    def get_signal_history(self, limit: int = 50, hours_limit: int = 0) -> List[Dict]:
        """
        Recupera histórico de sinais finalizados
        
        Args:
            limit (int): Número máximo de registros
            hours_limit (int): Se > 0, retorna apenas sinais das últimas N horas
        """
        if not self.client: return []
        
        try:
            query = self.client.table("signals") \
                .select("*") \
                .neq("status", "ACTIVE") \
                .order("timestamp", desc=True) \
                .limit(limit)
                
            # Filtro por tempo (retenção)
                
            # Execute query without .gt() filter to avoid type mismatch
            # We fetch a bit more than limit to allow for filtering
            if hours_limit > 0:
                query = query.limit(limit * 2) 
            
            response = query.execute()
            
            # Calculate cutoff for Python-side filtering
            cutoff = 0
            if hours_limit > 0:
                cutoff = int((time.time() - (hours_limit * 3600)) * 1000)

            results = []
            for row in response.data:
                # Preferimos o payload (objeto completo), senão usamos os dados da raiz
                sig_data = row.get("payload")
                
                # Normalize data source
                final_data = None
                if sig_data and isinstance(sig_data, dict) and "symbol" in sig_data:
                    final_data = sig_data
                elif row.get("symbol"):
                    final_data = row
                
                if final_data:
                    # Apply time filter if needed
                    ts = final_data.get("timestamp")
                    # Handle if timestamp is string (ISO) or int (Epoch)
                    is_valid = True
                    if hours_limit > 0 and ts:
                        try:
                            # If ts is large int/float -> epoch ms
                            if isinstance(ts, (int, float)):
                                if ts < cutoff: is_valid = False
                            # If ts is string, it might be ISO... skipping complex parsing for safety
                            # assuming our system saves as int/float ms based on signal_generator.py
                        except:
                            pass
                            
                    if is_valid:
                        results.append(final_data)
                        
            # Apply final limit after filtering
            return results[:limit]
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar histórico: {e}", flush=True)
            return []

    def count_labeled_signals(self) -> Dict:
        """Conta sinais por status para verificar dados disponíveis para ML"""
        if not self.client: return {"total": 0, "tp_hit": 0, "sl_hit": 0, "expired": 0}
        
        try:
            # Contagem por status
            tp_response = self.client.table("signals").select("id", count="exact").eq("status", "TP_HIT").execute()
            sl_response = self.client.table("signals").select("id", count="exact").eq("status", "SL_HIT").execute()
            exp_response = self.client.table("signals").select("id", count="exact").eq("status", "EXPIRED").execute()
            
            return {
                "tp_hit": tp_response.count or 0,
                "sl_hit": sl_response.count or 0,
                "expired": exp_response.count or 0,
                "total": (tp_response.count or 0) + (sl_response.count or 0) + (exp_response.count or 0)
            }
        except Exception as e:
            print(f"[DB ERROR] Erro ao contar sinais: {e}", flush=True)
            return {"total": 0, "tp_hit": 0, "sl_hit": 0, "expired": 0}

    def get_signals_with_features(self, limit: int = 500) -> List[Dict]:
        """Recupera sinais finalizados que possuem ai_features (otimizado para ML)"""
        if not self.client: return []
        
        try:
            response = self.client.table("signals") \
                .select("payload") \
                .neq("status", "ACTIVE") \
                .not_.is_("payload->ai_features", "null") \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            
            return [row["payload"] for row in response.data if row["payload"].get("ai_features")]
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar sinais com features: {e}", flush=True)
            return []

    # --- Métodos para Trading Plan ---

    def save_trading_plan(self, data: Dict):
        """Salva o plano de trading do usuário"""
        if not self.client: return
        
        try:
            payload = {
                "user_id": "default_user",
                "data": data
            }
            self.client.table("trading_plan").upsert(payload, on_conflict="user_id").execute()
        except Exception as e:
            print(f"[DB ERROR] Erro ao salvar plano de trading: {e}", flush=True)

    def get_trading_plan(self) -> Optional[Dict]:
        """Recupera o plano de trading do usuário"""
        if not self.client: return None
        
        try:
            response = self.client.table("trading_plan").select("data").eq("user_id", "default_user").execute()
            if response.data:
                return response.data[0]["data"]
            return None
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar plano de trading: {e}", flush=True)
            return None
