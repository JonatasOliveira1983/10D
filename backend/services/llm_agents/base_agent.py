from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """
    Abstract Base Class for all The Council agents.
    Each agent has a specific persona, a specialized task, and outputs a structured opinion.
    """
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def analyze(self, signal: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the signal and return a verdict.
        
        Returns:
            Dict containing:
            - score (0-100)
            - verdict ("APPROVED", "REJECTED", "NEUTRAL")
            - reasoning (str)
            - metadata (Dict)
        """
        pass

    def _format_prompt(self, template: str, **kwargs) -> str:
        """Helper to format prompts safely"""
        return template.format(**kwargs)
