"""
Base class for Maternal and Infant Healthcare Large Language Models.
Provides a unified interface across Chewie 1.2, MamaBot-Llama, and the Hybrid Router.
"""

from abc import ABC, abstractmethod
import time
import math
from typing import Dict, Any, Optional, List

class BaseHealthcareLLM(ABC):
    def __init__(
        self,
        name: str,
        model_family: str,
        parameter_size: str,
        developer: str,
        paradigm: str,
        device: str = "cpu"
    ):
        self.name = name
        self.model_family = model_family
        self.parameter_size = parameter_size
        self.developer = developer
        self.paradigm = paradigm
        self.device = device

    @abstractmethod
    def generate_response(
        self,
        query: str,
        matched_passage: Optional[str] = None,
        language: str = "en",
        triage_hint: Optional[str] = None,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a maternal/infant healthcare response given a query and clinical context.
        
        Returns:
            Dict containing:
                - model_name: str
                - response: str
                - urgency_category: str ('emergency', 'priority', 'routine')
                - latency_ms: float
                - tokens_generated: int
                - memory_allocated_mb: float
                - metadata: Dict[str, Any]
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model_family": self.model_family,
            "parameter_size": self.parameter_size,
            "developer": self.developer,
            "paradigm": self.paradigm,
            "device": self.device
        }

