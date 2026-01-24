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

    def evaluate_accuracy(self, metrics: Dict) -> bool:
        """Return True if accuracy is acceptable, False otherwise.
        Expected metrics dict contains key 'accuracy' (float between 0 and 1).
        """
        accuracy = metrics.get("accuracy")
        if accuracy is None:
            self.logger.warning("[MLSupervisor] No accuracy metric provided.")
            return False
        return accuracy >= self.accuracy_threshold

    def run(self, recent_metrics: Dict) -> Dict:
        """Assess recent model metrics and decide whether to allow trading.
        Returns a dict with keys:
            - allowed (bool): whether trading can proceed
            - reason (str): explanation
        """
        allowed = self.evaluate_accuracy(recent_metrics)
        if allowed:
            return {"allowed": True, "reason": "Model accuracy satisfactory."}
        else:
            return {"allowed": False, "reason": f"Model accuracy {recent_metrics.get('accuracy', 0):.2%} below threshold {self.accuracy_threshold:.2%}."}

    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes model performance context for the signal."""
        # Use metrics from market_context or defaults
        metrics = market_context.get("ml_metrics", {})
        allowed_data = self.run(metrics)
        
        return {
            "score": 100 if allowed_data["allowed"] else 0,
            "verdict": "APPROVED" if allowed_data["allowed"] else "REJECTED",
            "reasoning": allowed_data["reason"],
            "metadata": metrics
        }
