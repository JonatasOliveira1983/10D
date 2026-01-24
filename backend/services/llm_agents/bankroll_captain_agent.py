import logging
from typing import Dict, Any
from .base_agent import BaseAgent

class BankrollCaptainAgent(BaseAgent):
    """Agent responsible for bankroll management and risk exposure.
    It enforces a maximum of 20% of the total bankroll per trade, limits the
    number of concurrent elite slots (default 10), and can adjust stop‑loss
    to break‑even when conditions are met.
    """

    def __init__(self, max_exposure_pct: float = 20.0, max_slots: int = 10):
        super().__init__(name="bankroll_captain_agent", role="Bankroll Manager")
        self.max_exposure_pct = max_exposure_pct
        self.max_slots = max_slots
        self.logger = logging.getLogger(self.__class__.__name__)
        # Runtime state (could be persisted in DB in a real system)
        self.active_trades: Dict[str, Dict] = {}  # key: trade_id, value: trade data

    def can_open_trade(self, trade_amount: float, total_bankroll: float) -> bool:
        """Return True if opening a new trade respects exposure and slot limits."""
        exposure_ok = (trade_amount / total_bankroll) * 100 <= self.max_exposure_pct
        slots_ok = len(self.active_trades) < self.max_slots
        return exposure_ok and slots_ok

    def register_trade(self, trade_id: str, trade_data: Dict[str, Any]):
        """Add a trade to the internal tracking dictionary.
        trade_data should contain at least `amount` and `entry_price`.
        """
        self.active_trades[trade_id] = trade_data
        self.logger.info(f"[BankrollCaptain] Trade {trade_id} registered. Active trades: {len(self.active_trades)}")

    def deregister_trade(self, trade_id: str):
        """Remove a trade from tracking when it is closed or cancelled."""
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
            self.logger.info(f"[BankrollCaptain] Trade {trade_id} closed. Remaining: {len(self.active_trades)}")

    def evaluate_break_even(self, trade_id: str, current_price: float) -> bool:
        """Check if the trade can be moved to break‑even.
        Returns True if stop‑loss should be adjusted to entry price.
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        entry = trade.get("entry_price")
        sl = trade.get("stop_loss")
        # Simple rule: if profit >= 1.5 * (entry - sl) then move SL to entry
        if entry and sl and (current_price - entry) >= 1.5 * (entry - sl):
            trade["stop_loss"] = entry
            self.logger.info(f"[BankrollCaptain] Trade {trade_id} stop‑loss moved to break‑even.")
            return True
        return False

    def run(self, **kwargs) -> Dict[str, Any]:
        """Placeholder run method – in a real pipeline this would be called
        with the current bankroll state and a candidate trade to evaluate.
        It returns a dict with `allowed` (bool) and optional `reason`.
        """
        trade_amount = kwargs.get("trade_amount")
        total_bankroll = kwargs.get("total_bankroll")
        if trade_amount is None or total_bankroll is None:
            return {"allowed": False, "reason": "Missing trade_amount or total_bankroll"}
        allowed = self.can_open_trade(trade_amount, total_bankroll)
        reason = "" if allowed else "Exposure or slot limit exceeded"
        return {"allowed": allowed, "reason": reason}

    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes bankroll limits for the signal."""
        trade_amount = signal.get("amount", 0)
        total_bankroll = market_context.get("total_bankroll", 0)
        
        allowed_data = self.run(trade_amount=trade_amount, total_bankroll=total_bankroll)
        
        return {
            "score": 100 if allowed_data["allowed"] else 0,
            "verdict": "APPROVED" if allowed_data["allowed"] else "REJECTED",
            "reasoning": allowed_data["reason"],
            "metadata": {"slots_active": len(self.active_trades)}
        }
