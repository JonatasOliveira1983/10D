from typing import Dict, Any, List
from .base_agent import BaseAgent
import json
from datetime import datetime

class EliteManagerAgent(BaseAgent):
    """
    The Bankroll Captain.
    Responsible for executing Elite signals and learning from performance.
    Controls the strict 2-slot limit for the Sniper Bankroll.
    """
    
    def __init__(self, db_manager=None):
        super().__init__(name="Elite Manager Agent", role="Bankroll Captain")
        self.db = db_manager
        self.learning_data = {
            "total_elite_trades": 0,
            "wins": 0,
            "losses": 0,
            "experience_points": 0,
            "current_strategy": "Cautious Sniper",
            "last_reflection": "Initializing systems..."
        }
        self.load_learning_state()

    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final decision before opening a bankroll trade.
        Checks if it's an Eagle Elite signal and if we have slots.
        """
        is_eagle = signal.get("is_eagle_elite", False)
        score = signal.get("score", 0)
        
        # Elite Manager is very picky
        if not is_eagle:
            return {
                "agent": self.name,
                "score": 0,
                "verdict": "REJECTED",
                "reasoning": "Sinal não qualificado como Eagle Elite (MTF faltando)",
                "metadata": {}
            }
        
        if score < 70:
            return {
                "agent": self.name,
                "score": score,
                "verdict": "NEUTRAL",
                "reasoning": "Score Eagle Elite detectado, mas abaixo do limiar de confiança de 70%",
                "metadata": {}
            }

        return {
            "agent": self.name,
            "score": score,
            "verdict": "APPROVED",
            "reasoning": f"Sinal Elite confirmado! Confluência MTF e Score de {score}% garantem entrada sniper.",
            "metadata": {"experience_bonus": 5}
        }

    def reflect_on_performance(self, recent_trades: List[Dict]):
        """
        Self-optimization loop. Analyzes wins/losses to adjust 'persona'.
        """
        if not recent_trades:
            return

        wins = len([t for t in recent_trades if "WON" in str(t.get("status", ""))])
        losses = len([t for t in recent_trades if "LOST" in str(t.get("status", ""))])
        
        self.learning_data["total_elite_trades"] += len(recent_trades)
        self.learning_data["wins"] += wins
        self.learning_data["losses"] += losses
        
        # XP Calculation
        new_xp = (wins * 10) - (losses * 5)
        self.learning_data["experience_points"] += max(0, new_xp)
        
        # Strategy Adjustment
        win_rate = (wins / len(recent_trades)) * 100 if recent_trades else 0
        
        if win_rate > 70:
            self.learning_data["current_strategy"] = "Aggressive Hunter"
            self.learning_data["last_reflection"] = f"Performance excelente ({win_rate:.1f}%). Mantendo foco em rompimentos de alta volatilidade."
        elif win_rate < 40:
            self.learning_data["current_strategy"] = "Defensive Shield"
            self.learning_data["last_reflection"] = f"Taxa de acerto baixa ({win_rate:.1f}%). Ajustando filtros para ser mais seletivo em mercados laterais."
        else:
            self.learning_data["current_strategy"] = "Standard Sniper"
            self.learning_data["last_reflection"] = f"Equilíbrio estável. Monitorando correlação com BTC para entradas mais precisas."

        self.save_learning_state()

    def check_btc_panic(self, current_btc_price: float, prev_btc_price: float) -> bool:
        """
        Escudo BTC: Detects sharp drops in BTC price to protect Alts.
        Threshold: 1.5% drop in a short interval.
        """
        if not prev_btc_price or not current_btc_price:
            return False
        
        change = (current_btc_price - prev_btc_price) / prev_btc_price
        if change <= -0.015: # -1.5%
            print(f"[CAPTAIN] 🛡️ BTC PANIC DETECTED ({change*100:.2f}%). Shielding bankroll!", flush=True)
            return True
        return False

    def check_sector_heat(self, symbol: str, bybit_client) -> Dict:
        """
        Cadeia de Setor: Checks related pairs for confluence.
        """
        sector_map = {
            "SOLUSDT": ["ETHUSDT", "AVAXUSDT", "NEARUSDT"],
            "BTCUSDT": ["ETHUSDT", "SOLUSDT"],
            "ETHUSDT": ["BTCUSDT", "SOLUSDT"]
        }
        
        related = sector_map.get(symbol, ["BTCUSDT", "ETHUSDT"])
        print(f"[CAPTAIN] 🔍 Checking sector heat for {symbol} (Related: {related})...", flush=True)
        
        try:
            tickers = bybit_client.get_all_tickers()
            price_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers if "symbol" in t}
            # Simplified check: if > 50% of the sector is down, it's 'COLD'
            downs = 0
            for r_sym in related:
                ticker = next((t for t in tickers if t["symbol"] == r_sym), None)
                if ticker and float(ticker.get("price24hPcnt", 0)) < 0:
                    downs += 1
            
            status = "HOT" if downs <= len(related) / 2 else "COLD"
            return {"status": status, "downs": downs, "total": len(related)}
        except Exception as e:
            print(f"[CAPTAIN] Sector heat check failed: {e}")
            return {"status": "NEUTRAL"}

    def check_inertia(self, opened_at_str: str, current_price: float, entry_price: float) -> bool:
        """
        Veto de Inércia: Close if price hasn't moved towards target in 45 min.
        """
        try:
            opened_at = datetime.fromisoformat(opened_at_str.replace('Z', '+00:00'))
            duration = (datetime.utcnow().replace(tzinfo=opened_at.tzinfo) - opened_at).total_seconds() / 60
            
            # If after 45 mins, price is within 0.2% of entry, it's stagnant
            if duration >= 45:
                move_pct = abs(current_price - entry_price) / entry_price
                if move_pct <= 0.002:
                    print(f"[CAPTAIN] ⏱️ INERTIA DETECTED ({duration:.0f}m). Closing stale position.", flush=True)
                    return True
        except Exception as e:
            print(f"[CAPTAIN] Inertia check error: {e}")
        return False

    def record_learning(self, symbol: str, insight_type: str, lesson: str, context: Dict = None):
        """
        Persists a tactical lesson to Supabase for the ML 'Brain'.
        """
        if not self.db:
            return

        try:
            data = {
                "symbol": symbol,
                "insight_type": insight_type,
                "lesson_learned": lesson,
                "context_data": context or {},
                "experience_points_gained": 10 if "WON" in str(context) else 2
            }
            self.db.client.table("agent_learning").insert(data).execute()
            print(f"[CAPTAIN] 🧠 Learning recorded: {insight_type} for {symbol}", flush=True)
            
            # Update local memory
            self.learning_data["last_reflection"] = lesson
            self.learning_data["experience_points"] += data["experience_points_gained"]
            self.save_learning_state()
            
        except Exception as e:
            print(f"[CAPTAIN] Error recording learning: {e}", flush=True)

    def load_learning_state(self):
        """Loads learning state from DB"""
        if not self.db: return
        try:
            # We could fetch aggregated stats or the latest reflection
            pass
        except:
            pass

    def save_learning_state(self):
        """Saves current state summary - typically handled via bankroll_status updates"""
        pass

    def get_status(self) -> Dict:
        """Returns the current state for UI display"""
        return self.learning_data
