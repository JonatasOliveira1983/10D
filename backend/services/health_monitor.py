import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import psutil
from .llm_agents.system_health_agent import SystemHealthAgent

class HealthMonitor:
    """
    Background service that monitors the 10D system's health.
    It collects technical vitals and uses the SystemHealthAgent for AI diagnostics.
    """
    
    def __init__(self, generator=None):
        self.generator = generator
        self.agent = SystemHealthAgent()
        self.vitals_history: List[Dict[str, Any]] = []
        self.latest_ai_analysis: Dict[str, Any] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.interval_seconds = 60 # Check vitals every 60s
        self.ai_interval_seconds = 300 # AI Analysis every 5 minutes
        self.last_ai_check = 0
        
    def start(self):
        """Starts the health monitoring thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[HEALTH] System Health Monitor started.", flush=True)

    def stop(self):
        """Stops the health monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def get_current_vitals(self) -> Dict[str, Any]:
        """Collects the latest system vitals from all components"""
        try:
            db_status = "STABLE"
            if self.generator and self.generator.db:
                if not self.generator.db.is_connected():
                    db_status = "DISCONNECTED"
                elif self.generator.db.is_connecting():
                    db_status = "CONNECTING"
            
            # API Latency check (using Bybit ping as proxy)
            api_latency = 0
            if self.generator and self.generator.client:
                start = time.time()
                try:
                    self.generator.client.get_server_time()
                    api_latency = int((time.time() - start) * 1000)
                except:
                    api_latency = -1 # Error
            
            vitals = {
                "timestamp": int(time.time() * 1000),
                "timestamp_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "components": {
                    "database": db_status,
                    "bybit_api": api_latency,
                    "scanner_active": self.generator.system_ready if self.generator else False,
                    "active_signals_count": len(self.generator.active_signals) if self.generator else 0
                }
            }
            return vitals
        except Exception as e:
            print(f"[HEALTH ERROR] Failed to collect vitals: {e}", flush=True)
            return {"error": str(e)}

    def _monitor_loop(self):
        """Continuous background monitoring loop"""
        while self.monitoring:
            try:
                vitals = self.get_current_vitals()
                self.vitals_history.append(vitals)
                
                # Keep only last 60 entries (1 hour of minute-by-minute data)
                if len(self.vitals_history) > 60:
                    self.vitals_history.pop(0)
                
                # Periodically run AI diagnostics
                if time.time() - self.last_ai_check >= self.ai_interval_seconds:
                    self._run_ai_diagnostics(vitals)
                    
                time.sleep(self.interval_seconds)
            except Exception as e:
                print(f"[HEALTH LOOP ERROR] {e}", flush=True)
                time.sleep(10)

    def _run_ai_diagnostics(self, current_vitals: Dict[str, Any]):
        """Invokes the SystemHealthAgent for AI assessment"""
        if not self.generator or not hasattr(self.generator, 'llm_brain') or not self.generator.llm_brain:
            print("[HEALTH] AI diagnostics skipped: LLM not available.", flush=True)
            return

        def llm_func(prompt):
            # Wrapper for the LLM call using the existing brain
            return self.generator.llm_brain.call_gemini(prompt)

        print("[HEALTH] Running AI diagnostics...", flush=True)
        analysis = self.agent.analyze_vitals(current_vitals, llm_func)
        self.latest_ai_analysis = analysis
        self.last_ai_check = time.time()
        print(f"[HEALTH] AI Assessment: {analysis.get('status')} (Score: {analysis.get('health_score')})", flush=True)

    def get_full_report(self) -> Dict[str, Any]:
        """Returns the complete health status for the API"""
        return {
            "vitals": self.vitals_history[-1] if self.vitals_history else {},
            "ai_analysis": self.latest_ai_analysis,
            "vitals_summary": {
                "history_length": len(self.vitals_history),
                "uptime": "N/A" # Could be implemented
            }
        }
