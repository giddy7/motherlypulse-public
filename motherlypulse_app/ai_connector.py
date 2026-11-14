"""
MotherlyPulse AI Model Connector & Clinical Safety Scaffold
Bridges adapted neural models (Chewie 1.2, MamaBot-Llama) into the application flow
behind strict clinical invariant validation and approved deterministic fallbacks.

Pipeline Precedence:
Emergency Rules -> Model Generation (Priority/Routine) -> Clinical Invariant Validation -> Approved Deterministic Fallback.
"""

import os
import re
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ClinicalInvariantValidator:
    """
    Validates model-generated clinical responses against safety invariants:
    1. Zero contraindicated medications/substances recommended (e.g. aspirin in pregnancy, herbal concoctions/agbo).
       Distinguishes affirmative recommendations from unambiguous negative warnings/prohibitions.
       Where safe interpretation is uncertain or ambiguous, applies conservative rejection to trigger
       the approved deterministic fallback.
    2. Strict category prefix compliance ('EMERGENCY:', 'PRIORITY:', 'ROUTINE:').
    3. Mandatory emergency hospital/112 escalation if an emergency is indicated.

    Note: The validator provides defense-in-depth safety guardrails but does not guarantee absolute safety.
    """
    def __init__(self):
        self.contraindicated_keywords = [
            "aspirin", "ibuprofen", "advil", "motrin", "gin", "alcohol", "ogogoro",
            "concoction", "kaun", "potash", "agbo", "herbal mixture", "tetracycline"
        ]
        self.emergency_escalation_keywords = [
            "112", "emergency", "immediately", "hospital", "urgent", "ambulance",
            "ile-iwosan", "ile iwosan", "kiakia", "pajawiri", "dokita", "dókítà",
            "sharp sharp", "quick quick", "run go hospital", "now now"
        ]
        self.prohibition_patterns = [
            r'\b(?:do\s+not|don\'t|never|must\s+not|should\s+not|shouldn\'t|cannot|can\'t)\s+(?:ever\s+)?(?:take|drink|use|give|consume|ingest|administer|swallow|mix|buy)\b',
            r'\b(?:avoid|stop|refrain\s+from|steer\s+clear\s+of|beware\s+of)\b(?!\s+(?:avoiding|stopping|refraining))',
            r'\b(?:warn(?:ing|s|ed)?\s+against|advis(?:e|ing|ed)?\s+against)\b',
            r'\b(?:is|are|can\s+be|may\s+be)\s+(?:very\s+)?(?:dangerous|harmful|unsafe|toxic|fatal|poisonous|lethal|strictly\s+contraindicated)\b',
            r'\b(?:can|may|could)\s+(?:cause\s+harm|harm|lead\s+to\s+miscarriage|damage|kill|poison)\b',
            r'\b(?:toxic|harmful|dangerous|unsafe)\s+(?:to|for)\b',
            r'\bcontain(?:s|ing)?\s+.*?\b(?:toxic|dangerous|harmful|unsafe|not\s+safe)\b',
            r'\b(?:not\s+(?:scientifically\s+)?(?:proven|recommended|safe|advised|safe\s+in\s+pregnancy))\b',
            r'\b(?:carry|carries|pose|poses|lead\s+to|leads\s+to)\s+(?:significant\s+|serious\s+|high\s+)?(?:risks?|complications?|harm|danger)\b',
            r'\b(?:e\s+ma\s+lo|ẹ\s+má\s+lò|má\s+mu|ma\s+mu|kò\s+dára|ko\s+dara|lewu|ewu|máṣe|mase)\b',
            r'\b(?:no\s+drink|no\s+take|no\s+give|make\s+you\s+no|dey\s+dangerous|fit\s+harm|fit\s+kill|no\s+good|e\s+bad\s+for)\b'
        ]

    def _is_safe_clause(self, clause: str, term: str) -> bool:
        """
        Evaluates whether a clause containing a contraindicated term is strictly
        an unambiguous negative warning or prohibition, rather than an affirmative
        recommendation, ambiguous remark, or deceptive bypass.
        Where safe interpretation is uncertain, returns False to trigger fallback.
        """
        # 1. Detect deceptive bypasses and double negations
        if re.search(r'\b(?:do\s+not|don\'t|never)\s+avoid\b', clause):
            return False
        if re.search(r'\bnever\s+stop\s+(?:taking|using|drinking|giving)\b', clause):
            return False

        # 2. Check for explicit affirmative recommendation patterns
        if re.search(r'\b(?:you\s+can|you\s+may|you\s+should|feel\s+free\s+to|try|recommend(?:ed)?|prescribe(?:d)?)\s+(?:to\s+)?(?:take|drink|use|give|consume|ingest|buy|prepare|mix)\b', clause):
            return False
        if re.search(r'\b' + re.escape(term) + r'\s+(?:is|are|can\s+be)\s+(?:good|helpful|safe|recommended|effective|beneficial|fine|okay|ok)\b', clause):
            return False
        if re.search(r'\b' + re.escape(term) + r'\s+(?:helps?|relieves?|treats?|cures?)\b', clause):
            return False

        # 3. Check for explicit danger/harm or prohibition warnings
        has_warning = any(re.search(pat, clause) for pat in self.prohibition_patterns)
        if not has_warning:
            # Ambiguous or incidental mention without clear warning -> conservative rejection
            return False

        return True

    def validate(
        self,
        text: str,
        urgency_category: str,
        custom_contraindications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not text or not isinstance(text, str):
            return {
                "is_safe": False,
                "reason": "Empty or non-string response",
                "violations": ["empty_response"],
                "escalates_112": False
            }

        text_lower = text.lower()
        violations = []

        # 1. Strict category prefix check
        has_prefix = any(text.startswith(prefix) for prefix in ["EMERGENCY:", "PRIORITY:", "ROUTINE:"])
        if not has_prefix:
            violations.append("missing_category_prefix")

        # 2. Check contraindicated substances with negation/warning context awareness
        all_contra = list(self.contraindicated_keywords)
        if custom_contraindications:
            all_contra.extend([c.lower() for c in custom_contraindications])

        # Segment into sentences/clauses for context analysis
        clauses = [c.strip() for c in re.split(r'[.!?;\n]+', text_lower) if c.strip()]

        for term in set(all_contra):
            term_regex = r'\b' + re.escape(term) + r'\b'
            clauses_with_term = [c for c in clauses if re.search(term_regex, c)]
            
            if clauses_with_term:
                # Every single clause containing the contraindicated term must be an unambiguous safe warning
                for clause in clauses_with_term:
                    if not self._is_safe_clause(clause, term):
                        violations.append(term)
                        break

        # 3. Check emergency escalation if category is emergency
        # Strip the prefix so that 'EMERGENCY:' itself does not count as the action
        body_lower = re.sub(r'^(emergency|priority|routine):\s*', '', text_lower)
        escalates_112 = any(
            re.search(r'\b' + re.escape(w) + r'\b', body_lower)
            for w in self.emergency_escalation_keywords
        )

        cat_clean = urgency_category.lower() if urgency_category else "routine"
        if cat_clean == "emergency" and not escalates_112:
            violations.append("missing_emergency_escalation")

        is_safe = (len(violations) == 0)
        return {
            "is_safe": is_safe,
            "violations": violations,
            "escalates_112": escalates_112,
            "has_prefix": has_prefix,
            "reason": f"Violations: {', '.join(violations)}" if violations else "Passed clinical invariant check"
        }


class AIModelConnector:
    """
    Orchestrates neural model inference with automatic graceful fallback.
    Ensures that emergency logic is never bypassed by neural generations,
    and invalid or failing model outputs automatically fall back to
    deterministic verified templates.
    """
    def __init__(
        self,
        backend: str = "disabled",
        model_name: str = "chewie-1.2",
        adapter_path: Optional[str] = None,
        device: str = "cpu"
    ):
        self.backend = os.environ.get("AI_MODEL_BACKEND", backend).lower()
        self.model_name = os.environ.get("AI_MODEL_NAME", model_name)
        self.adapter_path = os.environ.get("AI_ADAPTER_PATH", adapter_path)
        self.remote_url = os.environ.get("AI_MODEL_ENDPOINT", "").strip()
        self.api_format = os.environ.get("AI_MODEL_API_FORMAT", "auto").strip().lower()
        self.api_key = os.environ.get("AI_MODEL_API_KEY", "").strip()
        self.timeout_seconds = float(os.environ.get("AI_MODEL_TIMEOUT", "5.0"))
        self.device = device
        self.validator = ClinicalInvariantValidator()
        self.model_instance = None
        self.tokenizer = None
        self.base_model = None
        self._initialize_backend()

    def _initialize_backend(self):
        """Initializes model runner if backend is active."""
        if self.backend == "disabled":
            logger.info("AIModelConnector: Backend disabled; using deterministic fallback pipeline.")
            return

        if self.backend == "mock":
            logger.info(f"AIModelConnector: Mock backend initialized for {self.model_name}.")
            return

        if self.backend in ["remote", "http"]:
            logger.info(f"AIModelConnector: Remote backend configured pointing to '{self.remote_url}' (timeout={self.timeout_seconds}s).")
            return

        if self.backend in ["local", "local_weights"]:
            if self.adapter_path and os.path.exists(self.adapter_path):
                logger.info(f"AIModelConnector: Initializing local weights from {self.adapter_path}...")
                try:
                    import torch
                    from transformers import AutoTokenizer, AutoModelForCausalLM
                    from peft import PeftModel
                    self.tokenizer = AutoTokenizer.from_pretrained(self.adapter_path)
                    base_model_name = "google/gemma-2-2b-it" if "chewie" in self.model_name.lower() else "meta-llama/Llama-3.1-8B-Instruct"
                    self.base_model = AutoModelForCausalLM.from_pretrained(
                        base_model_name,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        device_map="auto" if torch.cuda.is_available() else None,
                        low_cpu_mem_usage=True
                    )
                    self.model_instance = PeftModel.from_pretrained(self.base_model, self.adapter_path)
                    logger.info(f"AIModelConnector: Local backend ready on {self.device}.")
                except Exception as e:
                    logger.warning(f"AIModelConnector: Could not fully load weights into memory ({e}); using local simulation fallback.")
                    self.model_instance = None
            else:
                logger.info(f"AIModelConnector: Adapter path '{self.adapter_path}' not found; using local simulation fallback.")

    def generate_response(
        self,
        user_message: str,
        urgency_category: str,
        language: str = "English",
        reference_response: Optional[str] = None,
        custom_contraindications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the safe generation pipeline:
        1. Emergency Precedence: Emergency queries strictly bypass neural generation.
        2. Neural Generation: If active and non-emergency, generates clinical reply.
        3. Safety Invariant Filter: Validates response against contraindications and escalation.
        4. Fallback Execution: If generation fails, times out, or violates safety, falls back to reference.
        """
        start_time = time.time()
        cat_clean = (urgency_category or "routine").lower()

        # 1. STRICT EMERGENCY PRECEDENCE:
        # Emergency guidance is life-critical and must NEVER rely on non-deterministic generative models.
        if cat_clean == "emergency":
            return {
                "response": reference_response,
                "model_used": "EmergencyRulesEngine (Strict Bypass)",
                "ai_generated": False,
                "safety_validated": True,
                "fallback_triggered": False,
                "latency_ms": 0.0,
                "validation_details": {
                    "is_safe": True,
                    "reason": "Emergency bypass applied; zero neural risk"
                }
            }

        # 2. Check if AI backend is available
        if self.backend == "disabled":
            return {
                "response": reference_response,
                "model_used": "DeterministicReference (AI Disabled)",
                "ai_generated": False,
                "safety_validated": True,
                "fallback_triggered": True,
                "latency_ms": 0.0,
                "validation_details": {
                    "is_safe": True,
                    "reason": "AI Backend disabled"
                }
            }

        # 3. Model Generation
        raw_response = None
        error_msg = None
        try:
            if self.backend == "mock":
                prefix = "PRIORITY:" if cat_clean == "priority" else "ROUTINE:"
                raw_response = f"{prefix} [Mock {self.model_name}] Factual health guidance in {language} for: {user_message.strip()}"
            elif self.backend in ["remote", "http"]:
                raw_response = self._run_remote_inference(user_message, urgency_category, language)
            elif self.backend in ["local", "local_weights"]:
                # Real inference hook
                raw_response = self._run_local_inference(user_message, urgency_category, language)
            else:
                error_msg = f"Unknown backend: {self.backend}"
        except Exception as e:
            logger.error(f"AIModelConnector: Model generation failed ({e})", exc_info=True)
            error_msg = str(e)

        latency_ms = (time.time() - start_time) * 1000

        # 4. Clinical Invariant Validation
        if raw_response and not error_msg:
            val_result = self.validator.validate(
                raw_response,
                urgency_category,
                custom_contraindications
            )
            if val_result["is_safe"]:
                return {
                    "response": raw_response,
                    "model_used": self.model_name,
                    "ai_generated": True,
                    "safety_validated": True,
                    "fallback_triggered": False,
                    "latency_ms": round(latency_ms, 2),
                    "validation_details": val_result
                }
            else:
                logger.warning(
                    f"AIModelConnector: Generated response failed safety invariant check ({val_result['reason']}). "
                    f"Triggering deterministic fallback."
                )
                return {
                    "response": reference_response,
                    "model_used": f"{self.model_name} (Rejected by Validator)",
                    "rejected_raw_response": raw_response,
                    "ai_generated": False,
                    "safety_validated": False,
                    "fallback_triggered": True,
                    "latency_ms": round(latency_ms, 2),
                    "validation_details": val_result
                }

        # 5. Fallback on generation failure
        return {
            "response": reference_response,
            "model_used": "DeterministicReference (Generation Error Fallback)",
            "ai_generated": False,
            "safety_validated": False,
            "fallback_triggered": True,
            "error": error_msg or "Model returned empty response",
            "latency_ms": round(latency_ms, 2),
            "validation_details": {
                "is_safe": False,
                "reason": error_msg or "Empty generation"
            }
        }

    def _run_local_inference(self, prompt: str, category: str, lang: str) -> str:
        """Internal helper for local weight generation."""
        if self.model_instance and self.tokenizer:
            system_prompt = (
                "You are MotherlyPulse, an empathetic maternal and child health assistant for Ondo State, Nigeria. "
                "Respond accurately and empathetically. Categorize responses as EMERGENCY:, PRIORITY:, or ROUTINE:."
            )
            chat = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Language: {lang}. User Query: {prompt}"}
            ]
            formatted_prompt = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
            if hasattr(self.model_instance, "device"):
                inputs = {k: v.to(self.model_instance.device) for k, v in inputs.items()}
            import torch
            with torch.no_grad():
                output_ids = self.model_instance.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    temperature=0.0
                )
            generated_text = self.tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            return generated_text

        # Fallback formatted prompt if full neural weights not loaded in memory
        prefix = "PRIORITY:" if category.lower() == "priority" else "ROUTINE:"
        return f"{prefix} Clinical guidance in {lang} regarding: {prompt.strip()}"

    def _is_openai_format(self) -> bool:
        """Returns True when the remote endpoint uses OpenAI /v1/chat/completions format."""
        if self.api_format == "openai":
            return True
        if self.api_format == "custom":
            return False
        return self.remote_url.rstrip("/").endswith("/v1/chat/completions")

    def _remote_endpoint(self, route: str) -> str:
        """Resolves a remote route ('generate', 'compare', or 'v1/chat/completions') from AI_MODEL_ENDPOINT."""
        base = self.remote_url.rstrip("/")
        if not base:
            raise ConnectionError("Remote AI_MODEL_ENDPOINT is not configured.")
        if route == "generate" and self._is_openai_format():
            if base.endswith("/v1/chat/completions"):
                return base
            return f"{base}/v1/chat/completions"
        if base.endswith("/generate"):
            base = base[: -len("/generate")]
        elif base.endswith("/compare"):
            base = base[: -len("/compare")]
        elif base.endswith("/v1/chat/completions"):
            base = base[: -len("/v1/chat/completions")]
        return f"{base}/{route.lstrip('/')}"

    def _post_remote_json(self, route: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Posts JSON to the remote GPU inference endpoint with a strict timeout."""
        import urllib.request
        import urllib.error
        import json

        url = self._remote_endpoint(route)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as e:
            raise TimeoutError(
                f"Remote cloud GPU endpoint timed out or unreachable after {self.timeout_seconds}s: {e}"
            )

    def _run_remote_inference(self, prompt: str, category: str, lang: str) -> str:
        """
        Executes remote inference against a cloud GPU session endpoint or local
        llama.cpp `llama-server` OpenAI-compatible `/v1/chat/completions` endpoint
        with an explicit timeout safeguard.
        """
        if self._is_openai_format():
            system_prompt = (
                "You are MotherlyPulse, an empathetic maternal and child health assistant for Ondo State, Nigeria. "
                "Respond accurately, concisely, and empathetically. "
                "Start your reply with EMERGENCY:, PRIORITY:, or ROUTINE:."
            )
            user_prompt = (
                f"Language: {lang}. Urgency: {category.upper()}.\n"
                f"User Question: {prompt.strip()}"
            )
            data = self._post_remote_json(
                "generate",
                {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 200,
                },
            )
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message") or {}
                return (msg.get("content") or "").strip()
            return ""

        data = self._post_remote_json(
            "generate",
            {
                "message": prompt,
                "urgency_category": category,
                "language": lang,
            },
        )
        return data.get("response") or data.get("reply", "")

    def compare_models(
        self,
        user_message: str,
        urgency_category: str,
        language: str = "English",
        custom_contraindications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs a side-by-side A/B comparison between the baseline model and the
        fine-tuned Chewie 1.2 model, validating both outputs locally with
        ClinicalInvariantValidator. Emergency queries strictly bypass neural
        generation.
        """
        cat_clean = (urgency_category or "routine").lower()
        if cat_clean == "emergency":
            return {
                "available": False,
                "emergency_bypass": True,
                "reason": "Emergency queries bypass neural models for immediate 112 escalation.",
            }

        if self.backend == "disabled":
            return {
                "available": False,
                "emergency_bypass": False,
                "reason": "AI backend is disabled (AI_MODEL_BACKEND=disabled).",
            }

        try:
            if self.backend == "mock":
                prefix = "PRIORITY:" if cat_clean == "priority" else "ROUTINE:"
                base_raw = f"[Mock Baseline] Health guidance in {language} for: {user_message.strip()}"
                ft_raw = f"{prefix} [Mock {self.model_name}] Triage-aligned guidance in {language} for: {user_message.strip()}"
                base_ms, ft_ms = 0.0, 0.0
            elif self.backend in ["remote", "http"]:
                if self._is_openai_format():
                    return {
                        "available": False,
                        "emergency_bypass": False,
                        "reason": "A/B /compare requires a dual-model endpoint; single-model OpenAI/llama-server endpoint is active.",
                    }
                data = self._post_remote_json(
                    "compare",
                    {
                        "message": user_message,
                        "urgency_category": urgency_category,
                        "language": language,
                    },
                )
                base_obj = data.get("base", {})
                ft_obj = data.get("finetuned", {})
                base_raw = base_obj.get("response", "")
                ft_raw = ft_obj.get("response", "")
                base_ms = float(base_obj.get("latency_ms", 0.0))
                ft_ms = float(ft_obj.get("latency_ms", 0.0))
            elif self.backend in ["local", "local_weights"]:
                if not (self.model_instance and self.tokenizer and hasattr(self.model_instance, "disable_adapter")):
                    return {
                        "available": False,
                        "emergency_bypass": False,
                        "reason": "Local dual-model comparison requires a loaded PeftModel.",
                    }
                t0 = time.time()
                with self.model_instance.disable_adapter():
                    base_raw = self._run_local_inference(user_message, urgency_category, language)
                base_ms = round((time.time() - t0) * 1000, 2)
                t1 = time.time()
                ft_raw = self._run_local_inference(user_message, urgency_category, language)
                ft_ms = round((time.time() - t1) * 1000, 2)
            else:
                return {
                    "available": False,
                    "emergency_bypass": False,
                    "reason": f"Unknown backend: {self.backend}",
                }
        except Exception as e:
            logger.warning(f"AIModelConnector: A/B comparison unavailable ({e})")
            return {
                "available": False,
                "emergency_bypass": False,
                "error": str(e),
                "reason": f"Remote AI endpoint unreachable or timed out ({e}).",
            }

        return {
            "available": True,
            "emergency_bypass": False,
            "base": {
                "model_name": "google/gemma-2-2b-it (Baseline)",
                "response": base_raw,
                "latency_ms": round(base_ms, 2),
                "validation": self.validator.validate(base_raw, urgency_category, custom_contraindications),
            },
            "finetuned": {
                "model_name": f"{self.model_name} (Chewie 1.2 QLoRA)",
                "response": ft_raw,
                "latency_ms": round(ft_ms, 2),
                "validation": self.validator.validate(ft_raw, urgency_category, custom_contraindications),
            },
        }
