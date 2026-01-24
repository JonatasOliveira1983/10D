import logging
from typing import Dict, Any
from .base_agent import BaseAgent

class MLSupervisorAgent(BaseAgent):
    """Agent that supervises the ML predictor's performance.
    It checks recent accuracy metrics and can veto trades or request retraining.
    """

    def __init__(self, accuracy_threshold: float = 0.55):
        super().__init__(name="ml_supervisor_agent", role="ML Supervisor")
        self.accuracy_threshold = accuracy_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_status = "INITIALIZING"

    def care_for_model(self, ml_predictor) -> Dict[str, Any]:
        """Manages model lifecycle: checks samples and triggers training."""
        if not ml_predictor:
            return {"status": "ERROR", "message": "Predictor not provided"}
        
        status = ml_predictor.get_status()
        samples = status.get("available_samples", 0)
        min_required = status.get("min_samples_required", 100)
        
        if not status.get("model_loaded"):
            self.model_status = f"WARMUP ({samples}/{min_required})"
            if samples >= min_required and not status.get("is_training"):
                self.logger.info(f"[MLSupervisor] Enough samples ({samples}). Triggering first training.")
                # We return a signal to the generator to trigger training
                return {"action": "TRAIN", "reason": "First training threshold reached"}
        else:
            acc = status.get("last_accuracy", 0)
            self.model_status = f"ONLINE (Acc: {acc:.2%})"
            
            # Auto-retrain logic managed by predictor, but supervisor can influence
            if status.get("samples_since_last_train", 0) >= status.get("auto_train_interval", 30):
                 if not status.get("is_training"):
                    return {"action": "TRAIN", "reason": "Incremental retraining"}

        return {"status": self.model_status, "samples": samples}

    def evaluate_accuracy(self, metrics: Dict) -> bool:
        """Return True if accuracy is acceptable or if we are in warmup."""
        accuracy = metrics.get("accuracy")
        if accuracy is None:
            # During warmup, we allow it but report it wasn't checked
            return True 
        return accuracy >= self.accuracy_threshold

    def run(self, recent_metrics: Dict) -> Dict:
        """Assess recent model metrics and decide whether to allow trading."""
        accuracy = recent_metrics.get("accuracy")
        if accuracy is None:
             return {"allowed": True, "reason": "Model in WARMUP mode. Using technical rules only."}
             
        allowed = accuracy >= self.accuracy_threshold
        if allowed:
            return {"allowed": True, "reason": f"Model accuracy {accuracy:.2%} satisfactory."}
        else:
            return {"allowed": False, "reason": f"Model accuracy {accuracy:.2%} below threshold {self.accuracy_threshold:.2%}."}

    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes model performance context for the signal."""
        predictor = market_context.get("ml_predictor")
        metrics = {}
        if predictor:
            stats = predictor.get_status()
            metrics = {
                "accuracy": stats.get("last_accuracy"),
                "samples": stats.get("available_samples"),
                "model_loaded": stats.get("model_loaded")
            }
        
        allowed_data = self.run(metrics)
        
        return {
            "score": 100 if allowed_data["allowed"] else 50, # Never 0 if warmup
            "verdict": "APPROVED" if allowed_data["allowed"] else "OBSERVATION",
            "reasoning": allowed_data["reason"],
            "metadata": {
                "model_status": self.model_status,
                **metrics
            }
        }
