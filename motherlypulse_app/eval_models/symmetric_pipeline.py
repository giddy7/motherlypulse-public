"""
Symmetric Evaluation Pipeline for MotherlyPulse
Ensures strict experimental symmetry across Chewie 1.2, MamaBot-Llama, and Hybrid Router:
All models share:
1. Identical upstream DynamicTriageClassifier (Red-flag emergency check & medication detection)
2. Identical Clinical Passage Retrieval (WHO 2016 ANC, WHO 2022 PNC, FMOH 2019)
3. Identical post-generation safety verification
"""

import os
import re
import pandas as pd
from typing import Dict, Any, Optional, List
from .base_model import BaseHealthcareLLM
from ..classifier import DynamicTriageClassifier

class SymmetricPipeline:
    def __init__(self, model: BaseHealthcareLLM):
        self.model = model
        self.classifier = DynamicTriageClassifier()
        self.passages = self._load_passages()

    def _load_passages(self) -> List[Dict[str, Any]]:
        passage_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "MotherlyPulse_Data", "02_Passages", "passages.csv"
        ))
        if os.path.exists(passage_path):
            try:
                df = pd.read_csv(passage_path)
                return df.to_dict(orient="records")
            except Exception:
                pass
        return []

    def retrieve_passage(self, query: str, topic: Optional[str] = None) -> Optional[str]:
        if not self.passages:
            return None
            
        q_lower = query.lower()
        if topic:
            t_lower = topic.lower()
            for p in self.passages:
                if str(p.get("topic", "")).lower() in t_lower or t_lower in str(p.get("topic", "")).lower():
                    return p.get("passage_text")

        # Fallback keyword match
        best_match = None
        max_matches = 0
        for p in self.passages:
            p_text = str(p.get("passage_text", "")).lower()
            matches = sum(1 for word in q_lower.split() if len(word) > 4 and word in p_text)
            if matches > max_matches:
                max_matches = matches
                best_match = p.get("passage_text")
                
        return best_match if max_matches > 0 else self.passages[0].get("passage_text")

    def run(
        self,
        query: str,
        language: str = "en",
        topic: Optional[str] = None,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes query through symmetrical safety scaffolding.
        """
        # 1. Upstream Triage & Medication Safety Check (Identical for all arms)
        triage_result = self.classifier.classify(query, conversation_history)
        urgency_hint = triage_result["urgency_category"]
        med_safety = triage_result["medication_safety_triggered"]

        # 2. Upstream Grounded Passage Retrieval (Identical for all arms)
        passage = self.retrieve_passage(query, topic)

        # 3. Model Generation (The isolated experimental variable)
        model_output = self.model.generate_response(
            query=query,
            matched_passage=passage,
            language=language,
            triage_hint=urgency_hint,
            conversation_history=conversation_history
        )

        response_text = model_output["response"]
        model_urgency = model_output["urgency_category"]

        # 4. Enforce Strict Prefix Format & Safety Compliance
        if urgency_hint == "emergency" and not response_text.startswith("EMERGENCY:"):
            response_text = f"EMERGENCY: {response_text}"
            model_urgency = "emergency"
        elif urgency_hint == "priority" and not (response_text.startswith("PRIORITY:") or response_text.startswith("EMERGENCY:")):
            response_text = f"PRIORITY: {response_text}"
            model_urgency = "priority"
        elif urgency_hint == "routine" and not (response_text.startswith("ROUTINE:") or response_text.startswith("PRIORITY:") or response_text.startswith("EMERGENCY:")):
            response_text = f"ROUTINE: {response_text}"

        return {
            "query": query,
            "language": language,
            "model_name": self.model.name,
            "urgency_hint": urgency_hint,
            "med_safety_triggered": med_safety,
            "evaluated_urgency": model_urgency,
            "response": response_text,
            "latency_ms": model_output["latency_ms"],
            "tokens_generated": model_output["tokens_generated"],
            "memory_allocated_mb": model_output["memory_allocated_mb"],
            "metadata": model_output.get("metadata", {})
        }

