import unittest
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.services.llm_agents.ml_supervisor_agent import MLSupervisorAgent

class TestMLSupervisorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = MLSupervisorAgent(accuracy_threshold=0.55)

    def test_evaluate_accuracy_above_threshold(self):
        metrics = {"accuracy": 0.60}
        self.assertTrue(self.agent.evaluate_accuracy(metrics))

    def test_evaluate_accuracy_below_threshold(self):
        metrics = {"accuracy": 0.50}
        self.assertFalse(self.agent.evaluate_accuracy(metrics))

    def test_run_allowed(self):
        metrics = {"accuracy": 0.70}
        result = self.agent.run(metrics)
        self.assertTrue(result["allowed"])
        self.assertIn("Model accuracy satisfactory", result["reason"])

    def test_run_not_allowed(self):
        metrics = {"accuracy": 0.40}
        result = self.agent.run(metrics)
        self.assertFalse(result["allowed"])
        self.assertIn("below threshold", result["reason"].lower())

    def test_analyze_approved(self):
        # Should approve if accuracy >= 0.55
        market_context = {"ml_metrics": {"accuracy": 0.60}}
        result = self.agent.analyze({}, market_context)
        self.assertEqual(result["verdict"], "APPROVED")
        self.assertEqual(result["score"], 100)

    def test_analyze_rejected(self):
        market_context = {"ml_metrics": {"accuracy": 0.50}}
        result = self.agent.analyze({}, market_context)
        self.assertEqual(result["verdict"], "REJECTED")
        self.assertEqual(result["score"], 0)

if __name__ == '__main__':
    unittest.main()
