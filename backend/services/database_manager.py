import os
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Lazy import - Supabase will be imported only when needed
Client = None  # Type hint placeholder


class DatabaseManager:
    """Gerenciador de conexão e operações com Supabase (PostgreSQL)"""
    
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_ANON_KEY")
        self.client = None
        self._connection_in_progress = False
        self._connection_thread = None
        
        print(f"[DB INIT] SUPABASE_URL present: {bool(self.url)}", flush=True)
        print(f"[DB INIT] SUPABASE_ANON_KEY present: {bool(self.key)}", flush=True)
        
        if self.url:
            print(f"[DB INIT] SUPABASE_URL value: {self.url[:50]}...", flush=True)
        if self.key:
            print(f"[DB INIT] SUPABASE_ANON_KEY length: {len(self.key)} chars", flush=True)
        
        if not self.url or not self.key:
            print("[DB ERROR] SUPABASE_URL ou SUPABASE_ANON_KEY nao encontradas no .env", flush=True)
            self.client = None
        else:
            # Start background connection immediately
            print("[DB INIT] Starting background Supabase connection...", flush=True)
            self.start_background_connection()
    
    def start_background_connection(self):
        """Start Supabase connection in background thread (non-blocking)"""
        if self._connection_in_progress or self.client is not None:
            return
        
        import threading
        
        self._connection_in_progress = True
        
        def connect_async():
            try:
                print("[DB ASYNC] Connecting to Supabase in background...", flush=True)
                from supabase import create_client as supabase_create_client
                self.client = supabase_create_client(self.url, self.key)
                print(f"[DB ASYNC] [OK] Supabase connected! URL: {self.url[:30]}...", flush=True)
            except Exception as e:
                print(f"[DB ASYNC ERROR] Failed to connect: {type(e).__name__}: {e}", flush=True)
            finally:
                self._connection_in_progress = False
        
        self._connection_thread = threading.Thread(target=connect_async, daemon=True)
        self._connection_thread.start()
    
    def is_connected(self) -> bool:
        """Check if Supabase is connected (non-blocking)"""
        return self.client is not None
    
    def is_connecting(self) -> bool:
        """Check if connection is in progress"""
        return self._connection_in_progress
    
    def _ensure_client(self, blocking: bool = False) -> bool:
        """Check if client is ready. Non-blocking by default."""
        if self.client is not None:
            return True
        
        if not self.url or not self.key:
            return False
        
        # If not blocking, just start background connection and return False
        if not blocking:
            if not self._connection_in_progress:
                self.start_background_connection()
            return False
        
        # Blocking mode: wait for connection (legacy behavior)
        try:
            print("[DB INIT] Lazy loading Supabase client (blocking)...", flush=True)
            import threading
            
            result = [None]
            error = [None]
            
            def create_client_thread():
                try:
                    from supabase import create_client as supabase_create_client
                    result[0] = supabase_create_client(self.url, self.key)
                except Exception as e:
                    error[0] = e
            
            thread = threading.Thread(target=create_client_thread, daemon=True)
            thread.start()
            thread.join(timeout=30.0)  # 30 second timeout for blocking mode
            
            if thread.is_alive():
                print("[DB WARN] Supabase connection timeout (30s) - continuing without DB", flush=True)
                return False
            elif error[0]:
                print(f"[DB ERROR] Falha ao conectar ao Supabase: {type(error[0]).__name__}: {error[0]}", flush=True)
                return False
            else:
                self.client = result[0]
                print(f"[DB] [OK] Conexao com Supabase estabelecida - URL: {self.url[:30]}...", flush=True)
                return True
                
        except Exception as e:
            print(f"[DB ERROR] Falha ao conectar ao Supabase: {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            self.client = None
            print("[DB WARN] Sistema continuara sem persistencia em banco de dados", flush=True)
            return False

    # --- Métodos para Sinais ---

    def save_signal(self, signal: Dict):
        """Salva ou atualiza um sinal no banco"""
        if not self._ensure_client(): return
        
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
                "score": int(signal.get("score", 0)),  # Convert to int for DB
                "status": signal.get("status", "ACTIVE"),
                "final_roi": int(signal.get("final_roi", 0)) if signal.get("final_roi") is not None else None,
                "timestamp": signal.get("timestamp"),
                "exit_timestamp": signal.get("exit_timestamp"),
                "highest_roi": signal.get("highest_roi", 0.0),
                "partial_tp_hit": signal.get("partial_tp_hit", False),
                "trailing_stop_active": signal.get("trailing_stop_active", False),
                "payload": signal # Objeto completo
            }
            
            self.client.table("signals").upsert(data).execute()
        except Exception as e:
            print(f"[DB ERROR] Erro ao salvar sinal {signal.get('symbol')}: {e}", flush=True)

    def get_active_signals(self) -> Dict[str, Dict]:
        """Recupera todos os sinais com status ACTIVE"""
        if not self._ensure_client(): return {}
        
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

    def get_signal_history(self, limit: int = 500, hours_limit: int = 240) -> List[Dict]:
        """
        Recupera histórico de sinais finalizados
        
        Args:
            limit (int): Número máximo de registros
            hours_limit (int): Se > 0, retorna apenas sinais das últimas N horas (padrão 10 dias)
        """
        if not self._ensure_client():
            print("[DB] get_signal_history: client is None", flush=True)
            return []
        
        try:
            print(f"[DB] get_signal_history: limit={limit}, hours_limit={hours_limit}", flush=True)
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
            print(f"[DB] get_signal_history: fetched {len(response.data)} rows from Supabase", flush=True)
            
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
            print(f"[DB] get_signal_history: returning {len(results[:limit])} signals", flush=True)
            return results[:limit]
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar histórico: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return []

    def count_labeled_signals(self) -> Dict:
        """Conta sinais por status para verificar dados disponíveis para ML"""
        if not self._ensure_client(): return {"total": 0, "tp_hit": 0, "sl_hit": 0, "expired": 0}
        
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
        if not self._ensure_client(): return []
        
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

    def log_agent_insight(self, agent_id: str, insight_type: str, message: str, details: Dict = None):
        """Salva logs de insights dos agentes para o frontend"""
        if not self._ensure_client(): return
        
        try:
            # Table: llm_insights (id, symbol, insight_type, content, confidence, outcome, created_at)
            # We map message to content for UI display
            payload = {
                "insight_type": f"{agent_id}|{insight_type}",
                "content": {
                    "message": message,
                    "details": details or {}
                },
                "confidence": details.get("confidence") if details else 0.5,
                "created_at": datetime.now().isoformat()
            }
            self.client.table("llm_insights").insert(payload).execute()
        except Exception as e:
            # Silent fail to not block main thread
            print(f"[DB LOG ERROR] Failed to log insight to llm_insights: {e}", flush=True)

    # --- Métodos para Trading Plan ---

    def save_trading_plan(self, data: Dict):
        """Salva o plano de trading do usuário"""
        if not self._ensure_client(): return
        
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
        if not self._ensure_client(): return None
        
        try:
            response = self.client.table("trading_plan").select("data").eq("user_id", "default_user").execute()
            if response.data:
                return response.data[0]["data"]
            return None
        except Exception as e:
            print(f"[DB ERROR] Erro ao recuperar plano de trading: {e}", flush=True)
            return None
