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
    
    def __init__(self, db_manager, bybit_client=None, push_service=None, log_callback=None, llm_brain=None):
        self.db = db_manager
        self.client = bybit_client # For fetching real-time prices if needed
        self.push_service = push_service # For mobile alerts
        self.log_callback = log_callback # For Real-Time UI Logs (The HUD)
        self.llm_brain = llm_brain # For "Brain" consultation
        
        # --- NEW RISK MANAGEMENT RULES (v3) ---
        self.MAX_SLOTS_TOTAL = 10         # Absolute max orders
        self.RISK_CAP_PCT = 0.20          # Max 20% of bankroll allowed in "Risk Exposure"
        self.LEVERAGE = 50
        self.ENTRY_PERCENT = 0.05         # 5% of CURRENT bankroll per trade (approx)
        self.MIN_SCORE_ELITE = 65 
        
        # Initialize the Elite Manager Agent (The Captain)
        self.elite_agent = EliteManagerAgent(db_manager=self.db)
        from services.llm_agents.fundamental_agent import FundamentalAgent
        from services.llm_agents.technical_agent import TechnicalAgent
        self.fundamental_agent = FundamentalAgent()
        self.technical_agent = TechnicalAgent()
        self.prev_btc_price = None
        
        # Cache for status to reduce DB calls (Careful with concurrency!)
        self.status_cache = None
        self.last_status_fetch = 0
    
    def get_status(self):
        """Fetch current bankroll status from Supabase (Persistent)"""
        # NOTE: We keep cache for DISPLAY, but for critical checks we will bypass it.
        if self.status_cache and (datetime.now().timestamp() - self.last_status_fetch < 1): # Reduced to 1s
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

    def _check_risk_exposure(self, status):
        """
        Calculates if we can open a new trade based on:
        1. Max Slots (10)
        2. Risk Cap (20% of Bankroll) - Dynamic Scaling
        """
        try:
            # FORCE FETCH open trades (Bypass cache for safety)
            res = self.db.client.table("bankroll_trades").select("*").eq("status", "OPEN").execute()
            open_trades = res.data or []
            
            # 1. Count Active Risky Trades
            risky_trades_count = 0
            risky_exposure = 0.0
            
            for trade in open_trades:
                entry_price = float(trade.get("entry_price", 0))
                stop_loss = float(trade.get("stop_loss", -1))
                direction = trade.get("direction", "SHORT")
                entry_size = float(trade.get("entry_size_usd", 0))
                
                is_risk_free = False
                if stop_loss > 0:
                    if direction == "LONG" and stop_loss >= entry_price:
                        is_risk_free = True
                    elif direction == "SHORT" and stop_loss <= entry_price:
                        is_risk_free = True
                
                if not is_risk_free:
                    risky_trades_count += 1
                    risky_exposure += entry_size

            # 2. Dynamic Slot Check (Only limit RISKY trades)
            # If a trade is Risk-Free, it doesn't consume a "Risk Slot".
            # We still keep a hard ceiling (e.g. 20) to prevent system overload, 
            # but MAX_SLOTS_TOTAL (10) now applies to RISKY trades only.
            if risky_trades_count >= self.MAX_SLOTS_TOTAL:
                return False, f"Slots de Risco cheios ({risky_trades_count}/{self.MAX_SLOTS_TOTAL}). Aguarde blindagem."
            
            # Hard system cap
            if len(open_trades) >= 20: 
                return False, "Capacidade máxima do sistema atingida (20 ordens)."

            # 3. Risk Exposure Check (Financial)
            # v3 Fix: Use Integer-Based Slot System.
            
            new_trade_size = status.get("entry_size_usd", 0)
            current_balance = status.get("current_balance", 0)
            max_risky_slots = int(self.RISK_CAP_PCT / self.ENTRY_PERCENT) # 0.20 / 0.05 = 4
            
            if risky_trades_count < max_risky_slots:
                # We have open risky slots. Allow entry.
                
                # Check physical margin availability (Leverage helps here, $1 controls $50).
                used_margin = sum([float(t.get("entry_size_usd", 0)) for t in open_trades])
                available_margin = current_balance - used_margin
                
                if available_margin < (new_trade_size * 0.9): # 10% buffer
                     return False, f"Saldo insuficiente para margem (Livre: ${available_margin:.2f})"
                
                return True, "OK"

            # If we are here, Risky Slots are full (e.g. 4/4).
            # We can ONLY open if one trade becomes Risk Free.
            return False, f"Slots de Risco cheios ({risky_trades_count}/{max_risky_slots}). Aguarde blindagem (Stop no Entry)."
            
        except Exception as e:
            print(f"[BANKROLL] Risk check failed: {e}", flush=True)
            return False, "Error in Risk Check"

    def assess_signal(self, signal):
        """Evaluates a signal for the Elite Bankroll."""
        # 1. Get Fresh Status
        status = self.get_status()
        if not status: return False
            
        # 2. Check Risk Rules (Dynamic)
        allowed, reason = self._check_risk_exposure(status)
        if not allowed:
            # print(f"[BANKROLL] Signal rejected: {reason}", flush=True) # Reduce noise
            return False
            
        # 3. Check Quality
        score = signal.get("score_breakdown", {}).get("rules_score", signal["score"])
        council_veto = signal.get("governor_veto", False)
        
        if score < self.MIN_SCORE_ELITE or council_veto:
            return False

        # 4. Captain Verdict
        open_trades = []
        try:
            res = self.db.client.table("bankroll_trades").select("*").eq("status", "OPEN").execute()
            open_trades = res.data or []
        except:
            pass

        verdict = self.elite_agent.analyze(signal, {
            "active_trades": open_trades,
            "total_bankroll": status.get("current_balance", 0),
            "entry_amount": status.get("entry_size_usd", 0)
        })
        if verdict["verdict"] != "APPROVED":
            return False

        # 5. Open Trade
        return self._open_trade(signal, status)

    def _open_trade(self, signal, status):
        """Executes the trade in Supabase"""
        try:
            # Use FIXED entry size from current cycle
            entry_size = status.get("entry_size_usd", 1.0) # Default small
            entry_price = float(signal.get("entry_price") or signal.get("close"))
            if not entry_price: return False

            symbol = signal["symbol"]
            
            # Determine Stop Loss (Initial)
            # Use Signal's SL if available, else 1% fallback
            stop_loss = signal.get("stop_loss")
            direction = signal.get("direction", "SHORT")
            
            if not stop_loss:
                stop_loss = entry_price * 1.01 if direction == "SHORT" else entry_price * 0.99
            
            new_trade = {
                "signal_id": str(signal.get("id", "")),
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": float(stop_loss), # NEW V3 Column
                "entry_size_usd": float(entry_size),
                "leverage": self.LEVERAGE,
                "status": "OPEN",
                "telemetry": "Capitão no comando. Risco calculado.",
                "cycle_number": status.get("cycle_number", 1),
                "opened_at": datetime.utcnow().isoformat()
            }
            
            self.db.client.table("bankroll_trades").insert(new_trade).execute()
            
            self.db.client.table("bankroll_trades").insert(new_trade).execute()
            
            msg = f"TRADE INICIADO: {symbol} | Risco: ${entry_size:.2f} | Alvo: 6% (Sniper)"
            print(f"[BANKROLL] {msg}", flush=True)
            if self.log_callback:
                self.log_callback("bankroll_captain_agent", "TRADE_OPEN", f"🦅 {msg}", new_trade)
            
            self.status_cache = None
            return True
            
        except Exception as e:
            print(f"[BANKROLL] Failed to open trade: {e}", flush=True)
            return False

    def _check_advanced_captain_logic(self, trade: dict, current_price: float) -> Tuple[bool, str]:
        """
        Runs the Advanced Captain Tactics (The Council of War).
        Returns: (should_close, reason)
        """
        symbol = trade["symbol"]
        entry_price = trade["entry_price"]
        direction = trade.get("direction", "SHORT")
        
        # Calculate ROI
        pnl_pct = (current_price - entry_price) / entry_price if direction == "LONG" else (entry_price - current_price) / entry_price
        roi = pnl_pct * self.LEVERAGE

        # --- 1. PROTECTION PHASE (The Shield) ---
        # Rule: If ROI > 1%, Move to Break-Even (Virtual stop logic here, actual mod handled by caller or separate updater)
        # For this function, we just check if we need to PANIC exit below a certain point if established.
        
        # --- 2. SURF PHASE (The Hunter) ---
        # Rule: If ROI > 2%, enter SURF MODE. 
        if roi >= 0.02:
            # Consult the Council
            market_context = {
                "btc_regime": "TRENDING", # TODO: Get real regime from DB/Service
                "sentiment_score": 60 # TODO: Get real sentiment
            }
            
            # Sentinel Check (Fundamental)
            # fund_verdict = self.fundamental_agent.analyze(trade, market_context)
            
            # Technical Check (Volatility/Smart Money)
            # We simulate Smart Money check here (L/S Ratio, Open Interest)
            # In real impl, technical_agent would fetch this.
            ls_ratio = 1.2 # Mock: Healthy
            open_interest = "RISING" # Mock
            
            # Logic: If OI is rising and we are winning, TREND IS STRONG. HOLD.
            if open_interest == "RISING":
                return False, f"MODO SURF 🏄: Tendência forte (OI subindo). Buscando 6%..."
                
        # --- 3. STANDARD DEFENSE (Panic / Inertia) ---
        
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

        # 3. TRAILING STOP PSICOLÓGICO (M5 EMA9) - Only if NOT in strong Surf Mode or if reversing harder
        if roi >= 0.5 and roi < 2.0: # Between 50% and 200% ROI, be careful
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
                # --- NEW: GENERATE LIVE TELEMETRY (THE CAPTAIN SPEAKS) ---
                telemetry = ""
                
                # Check for Break-Even Move (Risk Free)
                # If ROI > 1% AND Stop Loss is not yet at Entry Price
                trade_sl = float(trade.get("stop_loss") or -1)
                
                # 1. State: PROTECTION (Risk Free Transition)
                if roi >= 0.01:
                    # Check if we need to move SL to Entry (Break Even)
                    # For LONG: SL < Entry. For SHORT: SL > Entry.
                    needs_update = False
                    if direction == "LONG" and trade_sl < entry_price:
                        needs_update = True
                    elif direction == "SHORT" and trade_sl > entry_price:
                        needs_update = True
                        
                    if needs_update:
                        # MOVE SL TO ENTRY (Risk Free)
                        try:
                            self.db.client.table("bankroll_trades").update({
                                "stop_loss": entry_price,
                                "telemetry": f"🛡️ BLINDAGEM ATIVA. Stop movido para Entry (${entry_price}). Risco Zero."
                            }).eq("id", trade["id"]).execute()
                            print(f"[BANKROLL] 🛡️ {symbol} Risk-Free! SL moved to {entry_price}", flush=True)
                            trade_sl = entry_price # Local update for next logic
                        except Exception as e:
                            print(f"[BANKROLL] Failed to update SL: {e}")

                    telemetry = f"🛡️ BLINDAGEM ATIVA. ROI: {roi*100:.1f}%. Risco Zero. Aguardando explosão."
                    
                # 2. State: SURF (HUNTING)
                if roi >= 0.02:
                     # Calculate Dynamic Target (Mock)
                    telemetry = f"🦅 MODO SURF LIGADO. ROI: {roi*100:.1f}%. Monitorando Smart Money & Liquidações acima."
                    if captain_reason and "MODO SURF" in captain_reason:
                         telemetry = captain_reason # Use the detailed reason from check logic
                
                # 3. State: DEFENSE / OBSERVING
                elif should_close:
                    telemetry = f"🚨 {captain_reason}. Encerrando operação!"
                elif roi <= -0.3:
                    telemetry = f"⚠️ Pressão contrária. Escudo BTC pronto para saída defensiva."
                elif roi < 0.01:
                    telemetry = f"👁️ Capitão monitorando: {symbol}."
                
                # Update DB
                update_data = {
                    # "current_price": current_price, # Column missing in DB
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
                    # FINAL CHECK: Did we hit SL?
                    # Check against trade_sl if available, else hard -50%
                    hit_sl = False
                    if trade_sl > 0:
                        if direction == "LONG" and current_price <= trade_sl: hit_sl = True
                        if direction == "SHORT" and current_price >= trade_sl: hit_sl = True
                    
                    if hit_sl or roi <= -0.5:
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
            msg = f"Fechando {trade['symbol']} ({status_label}) PnL: ${pnl_usd:.2f} ({roi*100:.1f}%)"
            print(f"[BANKROLL] {msg}", flush=True)
            if self.log_callback:
                self.log_callback("bankroll_captain_agent", "TRADE_CLOSE", f"🏁 {msg}", {"pnl": pnl_usd, "roi": roi})
            
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
            
            # --- NEW COMPOUNDING RULES (Doubling) ---
            trades_in_cycle = bankroll_status.get("trades_in_cycle", 0) + 1
            base_balance = bankroll_status.get("base_balance", 20.0)
            entry_size_usd = bankroll_status.get("entry_size_usd", 1.0)
            cycle_number = bankroll_status.get("cycle_number", 1)
            
            msg_cycle = ""
            
            # Check if Bankroll DOUBLED the Base Balance
            if new_balance >= (base_balance * 2.0):
                # CYCLE COMPLETE! Level Up!
                cycle_number += 1
                old_base = base_balance
                base_balance = new_balance # Set new floor
                # Recalculate Entry Size (5% of NEW Base)
                entry_size_usd = base_balance * self.ENTRY_PERCENT
                trades_in_cycle = 0 # Reset cycle count just for tracking
                
                msg_cycle = f" [🚀 BANCA DOBRADA! (Cycle {cycle_number}) New Base: ${base_balance:.2f} | Entry: ${entry_size_usd:.2f}]"
                print(f"🏛️ [CAPTAIN] LEVEL UP! Banca saiu de ${old_base:.2f} para ${base_balance:.2f}. Aumentando lotes.", flush=True)

                # Check for Phase Transition (70/30) logic preserved
                if win_rate >= 70:
                    print(f"🏛️ [CAPTAIN] META 70/30 MANTIDA! Sistema voando.", flush=True)

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

