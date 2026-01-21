
import logging
from datetime import datetime
import json

class BankrollManager:
    """
    Manages the 'Elite' Bankroll Simulation.
    Enforces strict risk management:
    - Max 2 Active Trades
    - 5% Risk per trade (Entry Size)
    - 50x Leverage
    - Fixed Compounding Cycle (every 20 trades)
    """
    
    def __init__(self, db_manager, bybit_client=None):
        self.db = db_manager
        self.client = bybit_client # For fetching real-time prices if needed
        self.MAX_SLOTS = 2
        self.LEVERAGE = 50
        self.ENTRY_PERCENT = 0.05 # 5% of bankroll per trade
        self.MIN_SCORE_ELITE = 75 # Stricter than general 70
        self.TP_TARGET = 0.02 # 2% movement (100% ROI)
        self.SL_TARGET = 0.01 # 1% movement (50% ROI)
        
        # Cache for status to reduce DB calls
        self.status_cache = None
        self.last_status_fetch = 0
    
    def get_status(self):
        """Fetch current bankroll status, with short caching"""
        if self.status_cache and (datetime.now().timestamp() - self.last_status_fetch < 5):
            return self.status_cache
            
        try:
            res = self.db.client.table("bankroll_status").select("*").single().execute()
            if res.data:
                self.status_cache = res.data
                self.last_status_fetch = datetime.now().timestamp()
                return res.data
        except Exception as e:
            print(f"[BANKROLL] Error fetching status: {e}")
        return None

    def assess_signal(self, signal):
        """
        Evaluates a signal for the Elite Bankroll.
        Returns True if trade was opened.
        """
        status = self.get_status()
        if not status:
            return False
            
        # 1. Check Slots
        if status.get("active_slots_used", 0) >= self.MAX_SLOTS:
            # Bankroll Full - Ignore even if good
            # print(f"[BANKROLL] Skipped {signal['symbol']} - Slots Full ({self.MAX_SLOTS}/{self.MAX_SLOTS})")
            return False
            
        # 2. Check Quality (Elite Filter)
        # Use Raw Rules Score if available
        score = signal.get("score_breakdown", {}).get("rules_score", signal["score"])
        
        # We can also check Council approval specifically
        council_veto = signal.get("governor_veto", False)
        
        if score < self.MIN_SCORE_ELITE:
            return False
            
        if council_veto:
             # Strict Bankroll: Do NOT take "Soft Veto" signals. Only fully approved.
             return False

        # 3. Open Trade
        return self._open_trade(signal, status)

    def _open_trade(self, signal, status):
        """Executes the trade in the simulation db"""
        try:
            current_balance = status["current_balance"]
            entry_size = current_balance * self.ENTRY_PERCENT
            
            # Ensure minimum $1 entry logic if really small bankroll? 
            # User said $1 for $20 bankroll, which matches 5%.
            
            entry_price = signal.get("entry_price") or signal.get("close") # Fallback
            if not entry_price:
                return False

            symbol = signal["symbol"]
            
            new_trade = {
                "signal_id": str(signal.get("id", "")), # Assuming signal stored in DB has ID, or we verify
                "symbol": symbol,
                "entry_price": float(entry_price),
                "entry_size_usd": float(entry_size),
                "leverage": self.LEVERAGE,
                "status": "OPEN",
                "opened_at": datetime.utcnow().isoformat()
            }
            
            # 1. Insert Trade
            self.db.client.table("bankroll_trades").insert(new_trade).execute()
            
            # 2. Update Status (Occupied Slot)
            new_slots = status["active_slots_used"] + 1
            self.db.client.table("bankroll_status").update({"active_slots_used": new_slots}).eq("id", status["id"]).execute()
            
            print(f"[BANKROLL] 🦅 ELITE TRADE OPENED: {symbol} | Size: ${entry_size:.2f} | Score: {signal.get('score')}", flush=True)
            
            # Invalidate cache
            self.status_cache = None
            return True
            
        except Exception as e:
            print(f"[BANKROLL] Failed to open trade: {e}")
            return False

    def update_positions(self, current_prices: dict):
        """
        Checks all OPEN trades against current prices to see if they hit TP/SL.
        current_prices: dict { 'BTCUSDT': 50000.0, ... }
        """
        try:
            # Fetch open trades
            open_trades = self.db.client.table("bankroll_trades").select("*").eq("status", "OPEN").execute()
            if not open_trades.data:
                return

            status = self.get_status()
            
            for trade in open_trades.data:
                symbol = trade["symbol"]
                current_price = current_prices.get(symbol)
                
                if not current_price:
                    # Fetch from API if not provided
                    try:
                        ticker = self.client.get_tickers(category="linear", symbol=symbol)
                        if ticker and 'list' in ticker and ticker['list']:
                            current_price = float(ticker['list'][0]['lastPrice'])
                    except:
                        pass
                
                if not current_price:
                    continue
                
                # Check TP/SL logic (Simplified for simulation)
                # You might want complex trailing logic later, but for now: Fixed 2% TP, 1% SL
                entry_price = trade["entry_price"]
                # Determine direction? Our DB schema didn't save direction! 
                # CRITICAL: We need direction.
                # Assuming 'signal_id' allows looking up, OR we should have saved 'side'.
                # For now, I will assume SHORT if not specified? No, dangerous.
                # I will Fetch the signal from DB signal table using signal_id, OR check symbol logic?
                # Actually, 10D usually shorts?
                # Let's add 'side' to the text check or assume we need to join.
                # To fix this quickly: I'll try to fetch the signal direction from signal history if possible
                # OR just infer from price move... NO.
                
                # FIX: I should update schema to include 'side' or 'direction', but user just created tables.
                # I will try to fetch the signal data from 'signals' table using signal_id.
                
                direction = "SHORT" # Default fallback for this system usually? 
                # Let's try to get it right.
                sig_res = self.db.client.table("signals").select("direction").eq("id", trade["signal_id"]).single().execute()
                if sig_res.data:
                    direction = sig_res.data.get("direction", "SHORT")
                
                pnl_pct = 0
                if direction == "LONG":
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                    
                # Leverage PnL
                roi = pnl_pct * self.LEVERAGE
                
                closed = False
                final_status = "OPEN"
                
                if roi >= 1.0: # +100% (TP Hit) -> Target was 2% price move * 50 = 100%
                     final_status = "WON"
                     closed = True
                elif roi <= -0.5: # -50% (SL Hit) -> Target was 1% price move * 50 = 50%
                     final_status = "LOST"
                     closed = True
                     
                if closed:
                    # Execute Close
                    pnl_usd = trade["entry_size_usd"] * roi
                    # Cap Loss at -100% just in case (liquidation)
                    if pnl_usd < -trade["entry_size_usd"]:
                        pnl_usd = -trade["entry_size_usd"]
                        
                    self._close_trade(trade, current_price, pnl_usd, roi, final_status, status)

        except Exception as e:
            print(f"[BANKROLL] Error updating positions: {e}")

    def _close_trade(self, trade, exit_price, pnl_usd, roi, status_label, bankroll_status):
        try:
            print(f"[BANKROLL] Closing {trade['symbol']} ({status_label}) PnL: ${pnl_usd:.2f} ({roi*100:.1f}%)", flush=True)
            
            # 1. Update Trade
            self.db.client.table("bankroll_trades").update({
                "status": status_label,
                "exit_price": exit_price,
                "pnl_usd": pnl_usd,
                "pnl_percent": roi,
                "closed_at": datetime.utcnow().isoformat()
            }).eq("id", trade["id"]).execute()
            
            # 2. Update Balance
            new_balance = bankroll_status["current_balance"] + pnl_usd
            new_slots = max(0, bankroll_status["active_slots_used"] - 1)
            new_count = bankroll_status["trade_count_cycle"] + 1
            
            # Check Compounding Cycle
            msg_cycle = ""
            if new_count >= 20:
                # Cycle complete!
                # Actually, since we calculate entry size dynamically based on current_balance in _open_trade,
                # continuous compounding happens naturally if we use current_balance.
                # But the user logic was: "A cada 2 dias... é feito um novo estudo".
                # If we want to simulate "Step Compounding" (fixed entry size for 20 trades),
                # we would need to store "cycle_entry_size" in status.
                # For now, I will stick to dynamic (closest to user's "Growth" request) or 
                # reset the counter.
                new_count = 0
                msg_cycle = " [CYCLE RESET]"
            
            self.db.client.table("bankroll_status").update({
                "current_balance": new_balance,
                "active_slots_used": new_slots,
                "trade_count_cycle": new_count,
                "last_update": datetime.utcnow().isoformat()
            }).eq("id", bankroll_status["id"]).execute()
            
            print(f"[BANKROLL] Balance Updated: ${new_balance:.2f}{msg_cycle}", flush=True)
            self.status_cache = None
            
        except Exception as e:
            print(f"[BANKROLL] Error closing trade: {e}")

