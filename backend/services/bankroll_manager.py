import logging
from datetime import datetime
import json
from typing import List, Dict, Tuple, Optional
from services.llm_agents.elite_manager_agent import EliteManagerAgent

class BankrollManager:
    """
    Manages the 'Elite' Bankroll Simulation.
    Enforces strict risk management:
    - Max 2 Active Trades
    - 5% Risk per trade (Entry Size)
    - 50x Leverage
    - Fixed Compounding Cycle (every 20 trades)
    """
    
    def __init__(self, db_manager, bybit_client=None, push_service=None):
        self.db = db_manager
        self.client = bybit_client # For fetching real-time prices if needed
        self.push_service = push_service # For mobile alerts
        self.MAX_SLOTS = 2
        self.LEVERAGE = 50
        self.ENTRY_PERCENT = 0.05 # 5% of bankroll per trade
        self.MIN_SCORE_ELITE = 65 # Ultra-relaxed for demo
        self.TP_TARGET = 0.02 # 2% movement (100% ROI)
        self.SL_TARGET = 0.01 # 1% movement (50% ROI)
        
        # Initialize the Elite Manager Agent (The Captain)
        self.elite_agent = EliteManagerAgent(db_manager=self.db)
        self.prev_btc_price = None
        
        # Cache for status to reduce DB calls
        self.status_cache = None
        self.last_status_fetch = 0
    
    def get_status(self):
        """Fetch current bankroll status from Supabase (Persistent)"""
        if self.status_cache and (datetime.now().timestamp() - self.last_status_fetch < 5):
            return self.status_cache

        try:
            res = self.db.client.table("bankroll_status").select("*").eq("id", "elite_bankroll").single().execute()
            if res.data:
                status = res.data
                # Enrich with Agent Data
                status['elite_agent'] = self.elite_agent.get_status()
                status['neural_status'] = self.elite_agent.learning_data.get("current_strategy", "Ativo")
                
                # Active Slots check
                active_count = self.db.client.table("bankroll_trades").select("id", count="exact").eq("status", "OPEN").execute()
                status['active_slots_used'] = active_count.count or 0
                
                self.status_cache = status
                self.last_status_fetch = datetime.now().timestamp()
                return status
        except Exception as e:
            print(f"[BANKROLL] Error fetching status: {e}", flush=True)
        return None

    def assess_signal(self, signal):
        """Evaluates a signal for the Elite Bankroll."""
        status = self.get_status()
        if not status:
            return False
            
        # 1. Check Slots (Max 2)
        if status.get("active_slots_used", 0) >= self.MAX_SLOTS:
            return False
            
        # 2. Check Quality
        score = signal.get("score_breakdown", {}).get("rules_score", signal["score"])
        council_veto = signal.get("governor_veto", False)
        
        if score < self.MIN_SCORE_ELITE or council_veto:
            return False

        # 3. Captain Verdict
        verdict = self.elite_agent.analyze(signal, {"active_slots": status.get("active_slots_used", 0)})
        if verdict["verdict"] != "APPROVED":
            return False

        # 4. Open Trade
        return self._open_trade(signal, status)

    def _open_trade(self, signal, status):
        """Executes the trade in Supabase"""
        try:
            # Use FIXED entry size from current cycle
            entry_size = status.get("entry_size_usd", 50.0)
            entry_price = signal.get("entry_price") or signal.get("close")
            if not entry_price: return False

            symbol = signal["symbol"]
            
            new_trade = {
                "signal_id": str(signal.get("id", "")),
                "symbol": symbol,
                "direction": signal.get("direction", "SHORT"),
                "entry_price": float(entry_price),
                "entry_size_usd": float(entry_size),
                "leverage": self.LEVERAGE,
                "status": "OPEN",
                "telemetry": "Capitão assumiu o comando. Monitorando entrada...",
                "cycle_number": status.get("cycle_number", 1),
                "opened_at": datetime.utcnow().isoformat()
            }
            
            self.db.client.table("bankroll_trades").insert(new_trade).execute()
            
            print(f"[BANKROLL] 🦅 ELITE TRADE OPENED: {symbol} | Entry: ${entry_size:.2f} | Cycle: {new_trade['cycle_number']}", flush=True)
            self.status_cache = None
            return True
            
        except Exception as e:
            print(f"[BANKROLL] Failed to open trade: {e}", flush=True)
            return False

    def _check_advanced_captain_logic(self, trade: dict, current_price: float) -> Tuple[bool, str]:
        """
        Runs the 5 Advanced Captain Tactics for an OPEN trade.
        Returns: (should_close, reason)
        """
        symbol = trade["symbol"]
        
        # 1. ESCUDO BTC (Panic Protection)
        try:
            btc_ticker = self.client.get_ticker("BTCUSDT")
            if btc_ticker:
                current_btc = float(btc_ticker["lastPrice"])
                if self.elite_agent.check_btc_panic(current_btc, self.prev_btc_price):
                    self.prev_btc_price = current_btc
                    return True, "ESCUDO BTC: Queda brusca detectada"
                self.prev_btc_price = current_btc
        except:
            pass

        # 2. VETO DE INÉRCIA (Time-Stop)
        if self.elite_agent.check_inertia(trade["opened_at"], current_price, trade["entry_price"]):
            return True, "VETO DE INÉRCIA: Movimento lateral excessivo"

        # 3. TRAILING STOP PSICOLÓGICO (M5 EMA9)
        # Only active if ROI > 50%
        entry_price = trade["entry_price"]
        direction = trade.get("direction", "SHORT")
        pnl_pct = (current_price - entry_price) / entry_price if direction == "LONG" else (entry_price - current_price) / entry_price
        roi = pnl_pct * self.LEVERAGE

        if roi >= 0.5:
            try:
                from services.indicator_calculator import calculate_ema
                m5_candles = self.client.get_klines(symbol, "5", 30)
                if m5_candles:
                    closes = [c["close"] for c in m5_candles]
                    ema_values = calculate_ema(closes, 9)
                    if ema_values and ema_values[-1]:
                        ema9 = ema_values[-1]
                        if direction == "LONG" and current_price < ema9:
                            return True, f"SURF FINALIZADO: Quebra de M5 EMA9 (ROI: {roi*100:.1f}%)"
                        elif direction == "SHORT" and current_price > ema9:
                            return True, f"SURF FINALIZADO: Quebra de M5 EMA9 (ROI: {roi*100:.1f}%)"
            except Exception as e:
                print(f"[BANKROLL] EMA9 check failed: {e}")

        # 4. SETOR HEAT CHECK (Sector Analysis)
        # We check this periodically. For simplicity, if ROI < -0.2 and Sector is COLD, exit early.
        if roi <= -0.2:
            heat = self.elite_agent.check_sector_heat(symbol, self.client)
            if heat.get("status") == "COLD":
                return True, f"SAÍDA SETORIAL: Setor correlacionado em queda"

        return False, ""

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
                    # Fetch from API if not provided in batch
                    try:
                        ticker = self.client.get_tickers(category="linear", symbol=symbol)
                        if ticker and 'list' in ticker and ticker['list']:
                            current_price = float(ticker['list'][0]['lastPrice'])
                    except:
                        pass
                
                if not current_price:
                    continue
                
                entry_price = trade["entry_price"]
                direction = trade.get("direction", "SHORT")
                
                # If direction missing in trade record, fallback to signal lookup
                if not trade.get("direction"):
                     try:
                        sig_res = self.db.client.table("signals").select("direction").eq("id", trade["signal_id"]).single().execute()
                        if sig_res.data:
                            direction = sig_res.data.get("direction", "SHORT")
                     except:
                        pass

                pnl_pct = 0
                if direction == "LONG":
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                    
                # Leverage PnL
                roi = pnl_pct * self.LEVERAGE
                
                # --- NEW: ADVANCED CAPTAIN LOGIC (M1/M5/H1 Checks) ---
                should_close, captain_reason = self._check_advanced_captain_logic(trade, current_price)

                # --- NEW: GENERATE LIVE TELEMETRY (AGENT THOUGHTS) ---
                # Default telemetry
                telemetry = f"🛡️ Capitão monitorando: {symbol}. Direção: {direction}."
                if should_close:
                    telemetry = f"🚨 {captain_reason}. Encerrando operação!"
                elif roi >= 1.5:
                    telemetry = f"🌊 SURFANDO ONDA SNIPER! ROI: {roi*100:.1f}%. Monitorando exaustão no M5..."
                elif roi >= 0.5:
                    telemetry = f"🛡️ Proteção Breakeven Ativada. Buscando alvo de 6%..."
                elif roi <= -0.3:
                    telemetry = f"⚠️ Pressão contrária. Escudo BTC pronto para saída defensiva."

                # --- NEW: UPDATE LIVE STATE IN DB ---
                update_data = {
                    "current_price": current_price,
                    "current_roi": round(roi * 100, 2),
                    "telemetry": telemetry
                }

                closed = False
                final_status = "OPEN"
                
                # Decision Tree
                if should_close:
                    closed = True
                    final_status = f"FECHADO PELO CAPITÃO ({captain_reason})"
                    print(f"[BANKROLL] 🏛️ CAPTAIN EXIT triggered for {symbol}: {captain_reason}", flush=True)
                elif roi >= 3.0: # +300% (6% Price Move)
                    final_status = "WON (SNIPER 300%)"
                    closed = True
                elif roi <= -0.5: # -50% (1% Price Move)
                    final_status = "LOST (SL)"
                    closed = True
                
                if closed:
                    pnl_usd = trade["entry_size_usd"] * roi
                    # Clamp loss to 100% of collateral if needed (though we use 50x)
                    if pnl_usd < -trade["entry_size_usd"]: pnl_usd = -trade["entry_size_usd"]
                    self._close_trade(trade, current_price, pnl_usd, roi, final_status, status)
                else:
                    self.db.client.table("bankroll_trades").update(update_data).eq("id", trade["id"]).execute()

        except Exception as e:
            print(f"[BANKROLL] Error updating positions: {e}")

    def _close_trade(self, trade, exit_price, pnl_usd, roi, status_label, bankroll_status):
        """Finalizes the trade and updates the compounding cycle"""
        try:
            print(f"[BANKROLL] Closing {trade['symbol']} ({status_label}) PnL: ${pnl_usd:.2f} ({roi*100:.1f}%)", flush=True)
            
            # 1. Update Trade Table
            self.db.client.table("bankroll_trades").update({
                "status": status_label,
                "exit_price": exit_price,
                "pnl_usd": pnl_usd,
                "roi_pct": roi,
                "closed_at": datetime.utcnow().isoformat()
            }).eq("id", trade["id"]).execute()
            
            # 2. Calculate New Stats
            is_win = "WON" in status_label or roi > 0
            new_balance = bankroll_status["current_balance"] + pnl_usd
            new_wins = bankroll_status.get("wins", 0) + (1 if is_win else 0)
            new_losses = bankroll_status.get("losses", 0) + (0 if is_win else 1)
            total_history = bankroll_status.get("total_trades", 0) + 1
            win_rate = (new_wins / total_history) * 100 if total_history > 0 else 0
            
            # --- FIXED 20-TRADE CYCLE LOGIC ---
            trades_in_cycle = bankroll_status.get("trades_in_cycle", 0) + 1
            base_balance = bankroll_status.get("base_balance", 1000.0)
            entry_size_usd = bankroll_status.get("entry_size_usd", 50.0)
            cycle_number = bankroll_status.get("cycle_number", 1)
            
            msg_cycle = ""
            if trades_in_cycle >= 20:
                # CYCLE COMPLETE! Recalculate everything for the next 20
                cycle_number += 1
                base_balance = new_balance # The new reference for the next cycle
                entry_size_usd = base_balance * self.ENTRY_PERCENT
                trades_in_cycle = 0
                msg_cycle = f" [CYCLE {cycle_number} STARTED! New Entry: ${entry_size_usd:.2f}]"
                
                # Check for Phase Transition (70/30)
                if win_rate >= 70:
                    print(f"🏛️ [CAPTAIN] META 70/30 BATIDA! Próxima fase: Bybit Real Money Ready.", flush=True)

            # 3. Update Status Table
            self.db.client.table("bankroll_status").update({
                "current_balance": new_balance,
                "base_balance": base_balance,
                "entry_size_usd": entry_size_usd,
                "trades_in_cycle": trades_in_cycle,
                "total_trades": total_history,
                "cycle_number": cycle_number,
                "wins": new_wins,
                "losses": new_losses,
                "win_rate": win_rate,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", "elite_bankroll").execute()
            
            print(f"[BANKROLL] Balance Updated: ${new_balance:.2f} | WinRate: {win_rate:.1f}%{msg_cycle}", flush=True)
            self.status_cache = None
            
            # --- PWA PUSH NOTIFICATIONS ---
            if self.push_service:
                try:
                    # 1. Immediate Result Notification
                    emoji = "✅ GAIN" if is_win else "❌ LOSS"
                    symbol = trade['symbol']
                    roi_str = f"{roi*100:.1f}%"
                    title = f"{emoji} no {symbol}!"
                    body = f"Resultado: {status_label}\nROI: {roi_str}\nBanca Atual: ${new_balance:.2f}"
                    
                    self.push_service.send_notification("default_user", title, body)
                    
                    # 2. Cycle Closure Notification
                    if trades_in_cycle == 0: # Just reset
                        cycle_title = f"📊 Ciclo {cycle_number-1} Concluído!"
                        cycle_body = f"Banca: ${new_balance:.2f} ({win_rate:.1f}% WR)\nNovo Lote: ${entry_size_usd:.2f}\nBora pro Ciclo {cycle_number}! 🚀"
                        self.push_service.send_notification("default_user", cycle_title, cycle_body)
                        
                        # 3. Phase Transition logic notification
                        if win_rate >= 70:
                            trans_title = "🏆 META 70/30 ALCANÇADA!"
                            trans_body = "Bybit Real Money Ready. O Capitão validou a consistência histórica. 🦅"
                            self.push_service.send_notification("default_user", trans_title, trans_body)

                except Exception as p_err:
                    print(f"[BANKROLL] [WARN] Push notification failed: {p_err}", flush=True)

            # --- AGENT LEARNING (ML PERSISTENCE) ---
            try:
                # Capture tactical lesson
                lesson = f"Trade em {trade['symbol']} resultou em {status_label}. "
                if not is_win:
                    lesson += f"Analizando pressão contrária e timings de saída para evitar ROI de {roi*100:.1f}%."
                else:
                    lesson += f"Estratégia validada com ROI de {roi*100:.1f}%."
                
                self.elite_agent.record_learning(
                    symbol=trade['symbol'],
                    insight_type="LOSS_ANALYSIS" if not is_win else "TACTICAL_ADJUSTMENT",
                    lesson=lesson,
                    context={"roi": roi, "pnl": pnl_usd, "cycle": cycle_number}
                )
            except Exception as ml_err:
                print(f"[BANKROLL] [WARN] Agent Learning failed: {ml_err}", flush=True)
            
        except Exception as e:
            print(f"[BANKROLL] Error closing trade: {e}", flush=True)

