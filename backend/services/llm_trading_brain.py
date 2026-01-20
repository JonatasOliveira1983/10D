"""
LLM Trading Brain - Gemini-powered intelligence layer
Uses Gemini free tier to validate signals, optimize TPs, and analyze exit opportunities
"""

import os
import time
import json
from typing import Dict, Optional, List
from datetime import datetime
import hashlib
from services.llm_agents.council_manager import CouncilManager

# Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[LLM] [WARN] google-generativeai not installed. LLM features disabled.", flush=True)


class LLMTradingBrain:
    """Gemini-powered trading intelligence layer"""
    
    def __init__(self, config: Dict = None, rag_memory = None):
        self.config = config or {}
        self.model = None
        self.db_manager = None  # Reference to DatabaseManager for learning
        self.cache: Dict[str, Dict] = {}  # Simple in-memory cache
        self.cache_ttl = self.config.get("LLM_CACHE_TTL_SECONDS", 300)
        self.min_confidence = self.config.get("LLM_MIN_CONFIDENCE", 0.6)
        self.rag_memory = rag_memory
        self.council = CouncilManager(rag_memory=self.rag_memory) # Initialize The Council with RAG
        
        # Learning context cache (refreshed every 5 minutes)
        self.learning_context = None
        self.learning_context_timestamp = 0
        self.learning_context_ttl = 300  # 5 minutes
        
        # Rate limiting
        self.requests_this_minute = 0
        self.minute_start = time.time()
        self.max_requests_per_minute = 14  # Stay under 15 limit
        
        # Stats
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "validations_approved": 0,
            "validations_rejected": 0,
            "tp_optimizations": 0,
            "exit_analyses": 0,
            "errors": 0,
            "learning_context_refreshes": 0
        }
        
        self._initialize_model()
    
    def set_database_manager(self, db_manager):
        """Set database manager for historical data access"""
        self.db_manager = db_manager
        print("[LLM] [BRAIN] Database manager connected - Learning mode enabled", flush=True)

    def set_rag_memory(self, rag_memory):
        """Set RAG Memory engine"""
        self.rag_memory = rag_memory
        # Re-initialize council with new memory if needed, or set it directly
        self.council = CouncilManager(rag_memory=self.rag_memory)
        print("[LLM] [BRAIN] RAG Memory connected to Council", flush=True)
    
    def _get_pair_history(self, symbol: str, days: int = 30) -> Dict:
        """Get historical performance for a specific trading pair"""
        if not self.db_manager:
            return {}
        
        try:
            # Fetch last 200 signals for this analysis
            history = self.db_manager.get_signal_history(limit=200, hours_limit=days * 24)
            
            # Filter for specific symbol
            pair_trades = [s for s in history if s.get("symbol") == symbol]
            
            if not pair_trades:
                return {"trades": 0, "message": "No history for this pair"}
            
            tp_hits = [s for s in pair_trades if s.get("status") == "TP_HIT"]
            sl_hits = [s for s in pair_trades if s.get("status") == "SL_HIT"]
            
            avg_roi = sum(s.get("final_roi") or s.get("current_roi") or 0 for s in pair_trades) / len(pair_trades)
            
            return {
                "trades": len(pair_trades),
                "tp_hits": len(tp_hits),
                "sl_hits": len(sl_hits),
                "win_rate": round((len(tp_hits) / len(pair_trades)) * 100, 1) if pair_trades else 0,
                "avg_roi": round(avg_roi, 2),
                "last_result": pair_trades[0].get("status") if pair_trades else None
            }
        except Exception as e:
            print(f"[LLM] [WARN] Error getting pair history: {e}", flush=True)
            return {}
    
    def _get_system_stats(self) -> Dict:
        """Get overall system performance statistics"""
        if not self.db_manager:
            return {}
        
        try:
            counts = self.db_manager.count_labeled_signals()
            history = self.db_manager.get_signal_history(limit=500, hours_limit=240)  # 10 days
            
            total_completed = counts.get("tp_hit", 0) + counts.get("sl_hit", 0)
            
            # Stats by signal type
            signal_types = {}
            for s in history:
                sig_type = s.get("signal_type", "UNKNOWN")
                if sig_type not in signal_types:
                    signal_types[sig_type] = {"tp": 0, "sl": 0, "total": 0}
                signal_types[sig_type]["total"] += 1
                if s.get("status") == "TP_HIT":
                    signal_types[sig_type]["tp"] += 1
                elif s.get("status") == "SL_HIT":
                    signal_types[sig_type]["sl"] += 1
            
            # Best performing signal type
            best_type = None
            best_win_rate = 0
            for sig_type, stats in signal_types.items():
                if stats["total"] >= 5:  # Minimum sample
                    wr = (stats["tp"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                    if wr > best_win_rate:
                        best_win_rate = wr
                        best_type = sig_type
            
            return {
                "total_trades": counts.get("total", 0),
                "tp_hit": counts.get("tp_hit", 0),
                "sl_hit": counts.get("sl_hit", 0),
                "expired": counts.get("expired", 0),
                "win_rate": round((counts.get("tp_hit", 0) / total_completed) * 100, 1) if total_completed > 0 else 0,
                "signal_types": signal_types,
                "best_signal_type": best_type,
                "best_type_win_rate": round(best_win_rate, 1)
            }
        except Exception as e:
            print(f"[LLM] [WARN] Error getting system stats: {e}", flush=True)
            return {}
    
    def _build_learning_context(self, symbol: str = None) -> str:
        """Build learning context from historical data for LLM prompts"""
        # Check if we need to refresh
        if (time.time() - self.learning_context_timestamp > self.learning_context_ttl or 
            self.learning_context is None):
            
            system_stats = self._get_system_stats()
            self.learning_context = system_stats
            self.learning_context_timestamp = time.time()
            self.stats["learning_context_refreshes"] += 1
            print(f"[LLM] [REFRESH] Learning context refreshed - {system_stats.get('total_trades', 0)} trades analyzed", flush=True)
        
        # Build context string
        ctx = self.learning_context or {}
        
        context_parts = [
            "=== SYSTEM LEARNING CONTEXT (from Supabase) ==="
        ]
        
        # Overall stats
        if ctx.get("total_trades", 0) > 0:
            context_parts.append(f"Total historical trades: {ctx.get('total_trades')}")
            context_parts.append(f"Overall Win Rate: {ctx.get('win_rate', 0)}% ({ctx.get('tp_hit', 0)} wins / {ctx.get('tp_hit', 0) + ctx.get('sl_hit', 0)} completed)")
            context_parts.append(f"Expired (no hit): {ctx.get('expired', 0)}")
        
        # Best signal type
        if ctx.get("best_signal_type"):
            context_parts.append(f"Best performing signal type: {ctx.get('best_signal_type')} ({ctx.get('best_type_win_rate')}% win rate)")
        
        # Pair-specific stats
        if symbol:
            pair_stats = self._get_pair_history(symbol)
            if pair_stats.get("trades", 0) > 0:
                context_parts.append(f"\n{symbol} HISTORY (last 30 days):")
                context_parts.append(f"  - Trades: {pair_stats.get('trades')}")
                context_parts.append(f"  - Win Rate: {pair_stats.get('win_rate')}%")
                context_parts.append(f"  - Avg ROI: {pair_stats.get('avg_roi')}%")
                context_parts.append(f"  - Last result: {pair_stats.get('last_result')}")
        
        context_parts.append("=== END LEARNING CONTEXT ===\n")
        
        return "\n".join(context_parts)
    
    def _initialize_model(self):
        """Initialize Gemini model with API key"""
        if not GENAI_AVAILABLE:
            print("[LLM] [ERROR] Cannot initialize - google-generativeai not available", flush=True)
            return
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[LLM] [ERROR] GEMINI_API_KEY not found in environment", flush=True)
            return
        
        try:
            genai.configure(api_key=api_key)
            model_name = self.config.get("LLM_MODEL", "gemini-1.5-flash")
            self.model = genai.GenerativeModel(model_name)
            print(f"[LLM] [OK] Gemini model '{model_name}' initialized successfully", flush=True)
        except Exception as e:
            print(f"[LLM] [ERROR] Failed to initialize Gemini: {e}", flush=True)
            self.model = None
    
    def _check_rate_limit(self) -> bool:
        """Check and update rate limit. Returns True if request allowed."""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.minute_start >= 60:
            self.requests_this_minute = 0
            self.minute_start = current_time
        
        if self.requests_this_minute >= self.max_requests_per_minute:
            return False
        
        self.requests_this_minute += 1
        return True
    
    def _get_cache_key(self, prefix: str, data: Dict) -> str:
        """Generate cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        return f"{prefix}_{hashlib.md5(data_str.encode()).hexdigest()[:12]}"
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get cached response if still valid"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return entry["data"]
            else:
                del self.cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """Save response to cache"""
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
        
        # Limit cache size
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
    
    def _call_gemini(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Call Gemini API with rate limiting and error handling"""
        if not self.model:
            return None
        
        if not self._check_rate_limit():
            print("[LLM] [WARN] Rate limit reached, skipping call", flush=True)
            return None
        
        try:
            self.stats["total_requests"] += 1
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3  # Lower temperature for more consistent outputs
                )
            )
            return response.text
        except Exception as e:
            self.stats["errors"] += 1
            print(f"[LLM] [ERROR] Gemini API error: {e}", flush=True)
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from Gemini response"""
        if not response:
            return None
        
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def test_connection(self) -> Dict:
        """Test Gemini connection"""
        if not self.model:
            return {"status": "ERROR", "message": "Model not initialized"}
        
        try:
            response = self.model.generate_content("Say 'LLM Trading Brain Online' in exactly those words.")
            return {
                "status": "OK",
                "message": "Gemini connected successfully",
                "response": response.text[:100]
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def validate_signal_context(self, signal: Dict, market_context: Dict) -> Dict:
        """
        Validate signal using The Council (Multi-Agent Debate).
        """
        # Check cache first
        cache_data = {"signal": signal.get("symbol"), "dir": signal.get("direction"), "ctx": market_context}
        cache_key = self._get_cache_key("validate", cache_data)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Fallback if no model
        if not self.model:
            return {
                "approved": True,
                "confidence": 0.5,
                "reasoning": "LLM unavailable - using default approval",
                "suggested_action": "PROCEED"
            }
        
        # Define the LLM callback
        def llm_callback(prompt: str) -> str:
            return self._call_gemini(prompt, max_tokens=600)

        # Run The Council
        print(f"[COUNCIL] Convening The Council for {signal.get('symbol')}...", flush=True)
        result = self.council.conduct_debate(signal, market_context, llm_callback)
        
        if result:
            result.setdefault("approved", False)
            result.setdefault("suggested_action", "PROCEED" if result["approved"] else "SKIP")
            
            if result["approved"]:
                self.stats["validations_approved"] += 1
                print(f"[COUNCIL] [OK] APPROVED: {result.get('reasoning')}", flush=True)
            else:
                self.stats["validations_rejected"] += 1
                print(f"[COUNCIL] [X] REJECTED: {result.get('reasoning')}", flush=True)
            
            self._save_to_cache(cache_key, result)
            return result
        
        # Fallback
        return {
            "approved": True,
            "confidence": 0.5,
            "reasoning": "Council skipped (Technical Fallback)",
            "suggested_action": "PROCEED"
        }
    
    def suggest_optimal_tp(self, signal: Dict, market_context: Dict) -> Dict:
        """
        Suggest optimal TP based on market analysis.
        Returns: {"original_tp_pct": float, "suggested_tp_pct": float, "reasoning": str}
        """
        original_tp_pct = signal.get('dynamic_targets', {}).get('tp_pct', 2.0)
        
        # Check cache
        cache_data = {"symbol": signal.get("symbol"), "dir": signal.get("direction"), "orig_tp": original_tp_pct}
        cache_key = self._get_cache_key("tp_opt", cache_data)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        if not self.model:
            return {
                "original_tp_pct": original_tp_pct,
                "suggested_tp_pct": original_tp_pct,
                "reasoning": "LLM unavailable - using original TP",
                "should_adjust": False
            }
        
        # Get learning context for TP optimization
        learning_context = self._build_learning_context(signal.get('symbol'))
        
        prompt = f"""You are a crypto trading TP optimizer. Analyze if the Take Profit target should be adjusted.

{learning_context}

CURRENT SETUP:
- Symbol: {signal.get('symbol')}
- Direction: {signal.get('direction')}
- Current TP: {original_tp_pct}%
- RSI: {signal.get('rsi', 50)}
- BTC Regime: {market_context.get('btc_regime', 'TRENDING')}
- Decoupling Score: {market_context.get('decoupling_score', 0)}
- Signal Type: {signal.get('signal_type')}

RULES:
- RANGING market: Conservative TP (1-2%)
- TRENDING market: Standard TP (2-3%)  
- BREAKOUT market: Aggressive TP (3-6%)
- High decoupling (>0.6): Can push TP higher
- Extreme RSI (<20 or >80): Potential for larger moves
- CONSIDER HISTORY: If this pair usually hits TP (high win rate), be more aggressive. If it hits SL often, be conservative.

RESPOND IN JSON FORMAT ONLY:
{{
  "original_tp_pct": {original_tp_pct},
  "suggested_tp_pct": X.X,
  "reasoning": "Brief explanation citing history (max 30 words)",
  "should_adjust": true/false
}}"""

        response = self._call_gemini(prompt, max_tokens=200)
        result = self._parse_json_response(response)
        
        if result:
            result.setdefault("original_tp_pct", original_tp_pct)
            result.setdefault("suggested_tp_pct", original_tp_pct)
            result.setdefault("reasoning", "Analysis complete")
            result.setdefault("should_adjust", False)
            
            # Validate suggested TP is reasonable (1-8%)
            if result["suggested_tp_pct"] < 1:
                result["suggested_tp_pct"] = 1.0
            elif result["suggested_tp_pct"] > 8:
                result["suggested_tp_pct"] = 8.0
            
            self.stats["tp_optimizations"] += 1
            self._save_to_cache(cache_key, result)
            return result
        
        return {
            "original_tp_pct": original_tp_pct,
            "suggested_tp_pct": original_tp_pct,
            "reasoning": "LLM response parsing failed",
            "should_adjust": False
        }
    
    def analyze_exit_opportunity(self, signal: Dict, current_roi: float, market_momentum: Dict) -> Dict:
        """
        Analyze if position should be held, partially closed, or fully exited.
        Returns: {"action": "HOLD"|"PARTIAL"|"EXIT", "confidence": float, "reasoning": str}
        """
        # Check cache
        cache_data = {"symbol": signal.get("symbol"), "roi": round(current_roi, 2)}
        cache_key = self._get_cache_key("exit", cache_data)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        if not self.model:
            # Simple rule-based fallback
            if current_roi >= 4.0:
                action = "PARTIAL"
            elif current_roi >= 6.0:
                action = "EXIT"
            else:
                action = "HOLD"
            return {
                "action": action,
                "confidence": 0.5,
                "reasoning": "LLM unavailable - using rule-based exit"
            }
        
        # Get learning context for Exit analysis
        learning_context = self._build_learning_context(signal.get('symbol'))
        
        prompt = f"""You are a position manager for crypto trading. Decide the best exit action for this position.

{learning_context}

POSITION STATUS:
- Symbol: {signal.get('symbol')}
- Direction: {signal.get('direction')}
- Current ROI: {current_roi:.2f}%
- Original TP Target: {signal.get('dynamic_targets', {}).get('tp_pct', 2)}%
- Trailing Stop Active: {signal.get('trailing_stop_active', False)}
- Partial TP Hit: {signal.get('partial_tp_hit', False)}

MARKET MOMENTUM:
- Price trend: {market_momentum.get('trend', 'NEUTRAL')}
- Volume: {market_momentum.get('volume_status', 'NORMAL')}

INSTRUCTIONS:
- CONSIDER HISTORY: If this pair drops fast after this ROI levels historically, EXIT now.
- If market momentum is strong against us, EXIT.
- If we are close to historical average Max ROI for this pair, TAKE PROFIT.

ACTIONS:
- HOLD: Keep position, let it run to TP
- PARTIAL: Close 50% and move SL to entry
- EXIT: Close full position now

RESPOND IN JSON FORMAT ONLY:
{{
  "action": "HOLD" or "PARTIAL" or "EXIT",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation citing history (max 30 words)"
}}"""

        response = self._call_gemini(prompt, max_tokens=150)
        result = self._parse_json_response(response)
        
        if result:
            result.setdefault("action", "HOLD")
            result.setdefault("confidence", 0.5)
            result.setdefault("reasoning", "Analysis complete")
            
            # Validate action
            if result["action"] not in ["HOLD", "PARTIAL", "EXIT"]:
                result["action"] = "HOLD"
            
            self.stats["exit_analyses"] += 1
            self._save_to_cache(cache_key, result)
            return result
        
        return {
            "action": "HOLD",
            "confidence": 0.5,
            "reasoning": "LLM response parsing failed - holding position"
        }
    
    def analyze_market_sentiment(self, headlines: List[Dict]) -> Dict:
        """
        Analyze news headlines to determine market sentiment.
        headlines: List[{"title": str, "source": str, ...}]
        Returns: {"score": 0-100, "sentiment": "BEARISH"|"NEUTRAL"|"BULLISH", "summary": str}
        """
        if not headlines:
            return {"score": 50, "sentiment": "NEUTRAL", "summary": "No news available"}
        
        # Check cache (hash of latest headline title as key)
        latest_title = headlines[0].get("title", "") if headlines else ""
        cache_data = {"latest_head": latest_title, "count": len(headlines)}
        cache_key = self._get_cache_key("sentiment", cache_data)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        if not self.model:
            return {
                "score": 50, 
                "sentiment": "NEUTRAL", 
                "summary": "LLM unavailable for sentiment analysis"
            }

        # Prepare headlines for prompt
        headlines_text = "\n".join([f"- {h.get('title')}" for h in headlines[:15]])
        
        prompt = f"""You are a crypto market sentiment analyst. Analyze these headlines and determine the Fear & Greed score.

HEADLINES:
{headlines_text}

INSTRUCTIONS:
1. Score from 0 (Extreme Fear) to 100 (Extreme Greed).
   - 0-25: Extreme Fear (Bearish)
   - 26-45: Fear (Bearish)
   - 46-54: Neutral
   - 55-75: Greed (Bullish)
   - 76-100: Extreme Greed (Bullish)
2. Summarize the main narrative in ONE sentence IN PORTUGUESE (PT-BR).
3. The summary must be natural and avoid robotic phrasing.

RESPOND IN JSON FORMAT ONLY:
{{
  "score": 0-100,
  "sentiment": "BEARISH" or "NEUTRAL" or "BULLISH",
  "summary": "Resumo em Português"
}}"""

        response = self._call_gemini(prompt, max_tokens=150)
        result = self._parse_json_response(response)
        
        if result:
            result.setdefault("score", 50)
            result.setdefault("sentiment", "NEUTRAL")
            result.setdefault("summary", "Analysis complete")
            
            self._save_to_cache(cache_key, result)
            return result
            
        return {
            "score": 50,
            "sentiment": "NEUTRAL", 
            "summary": "Sentiment analysis failed"
        }

    def get_status(self) -> Dict:
        """Get LLM Brain status and statistics"""
        return {
            "enabled": self.model is not None,
            "model": self.config.get("LLM_MODEL", "gemini-1.5-flash"),
            "rate_limit": {
                "requests_this_minute": self.requests_this_minute,
                "max_per_minute": self.max_requests_per_minute
            },
            "cache": {
                "entries": len(self.cache),
                "ttl_seconds": self.cache_ttl
            },
            "stats": self.stats
        }
    
    def is_enabled(self) -> bool:
        """Check if LLM is properly initialized and enabled"""
        return self.model is not None
