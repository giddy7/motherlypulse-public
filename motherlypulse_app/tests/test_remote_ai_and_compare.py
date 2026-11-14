"""
Unit and integration tests for remote AI backend (`AI_MODEL_BACKEND=remote`),
timeout/offline fallback to DeterministicReference, and `/compare` A/B demo mode.
"""

import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from motherlypulse_app.ai_connector import AIModelConnector
from motherlypulse_app.user_store import UserStore
from motherlypulse_app.telegram_bot import TelegramBotHandler


class _DummyResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestRemoteAIAndCompare(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_remote_ai.db")
        self.user_store = UserStore(db_path=self.db_path)
        self.user_store.register_user(
            user_id="u_cmp_1",
            channel="telegram",
            language="English",
            user_group="pregnant_woman",
            alias="Ada",
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_remote_generate_success_and_auth_header(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "https://demo-tunnel.trycloudflare.com",
            "AI_MODEL_API_KEY": "secret-demo-key",
            "AI_MODEL_TIMEOUT": "10.0",
        }
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["auth"] = req.get_header("Authorization")
            return _DummyResponse({"response": "ROUTINE: Drink plenty of water and rest."})

        with patch.dict(os.environ, env, clear=False), patch("urllib.request.urlopen", side_effect=fake_urlopen):
            connector = AIModelConnector()
            res = connector.generate_response(
                user_message="I feel slightly tired today.",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Rest and hydrate.",
            )

        self.assertTrue(res["ai_generated"])
        self.assertTrue(res["safety_validated"])
        self.assertFalse(res["fallback_triggered"])
        self.assertEqual(res["response"], "ROUTINE: Drink plenty of water and rest.")
        self.assertEqual(captured["url"], "https://demo-tunnel.trycloudflare.com/generate")
        self.assertEqual(captured["timeout"], 10.0)
        self.assertEqual(captured["auth"], "Bearer secret-demo-key")

    def test_remote_endpoint_normalizes_trailing_generate(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "https://demo-tunnel.trycloudflare.com/generate",
        }
        with patch.dict(os.environ, env, clear=False):
            connector = AIModelConnector()
            self.assertEqual(
                connector._remote_endpoint("generate"),
                "https://demo-tunnel.trycloudflare.com/generate",
            )
            self.assertEqual(
                connector._remote_endpoint("compare"),
                "https://demo-tunnel.trycloudflare.com/compare",
            )

    def test_remote_timeout_and_unset_endpoint_fallback(self):
        # 1. Unset endpoint falls back cleanly
        with patch.dict(os.environ, {"AI_MODEL_BACKEND": "remote", "AI_MODEL_ENDPOINT": ""}, clear=False):
            connector = AIModelConnector()
            res = connector.generate_response(
                user_message="Mild backache",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Approved deterministic fallback.",
            )
        self.assertFalse(res["ai_generated"])
        self.assertTrue(res["fallback_triggered"])
        self.assertEqual(res["response"], "ROUTINE: Approved deterministic fallback.")

        # 2. Network/timeout error falls back cleanly
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "https://offline.trycloudflare.com",
            "AI_MODEL_TIMEOUT": "3.0",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            connector = AIModelConnector()
            res = connector.generate_response(
                user_message="Mild backache",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Approved deterministic fallback.",
            )
        self.assertFalse(res["ai_generated"])
        self.assertTrue(res["fallback_triggered"])
        self.assertEqual(res["response"], "ROUTINE: Approved deterministic fallback.")

    def test_remote_unsafe_output_rejected_by_validator(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "https://demo-tunnel.trycloudflare.com",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen",
            return_value=_DummyResponse({"response": "ROUTINE: You can take aspirin for headache."}),
        ):
            connector = AIModelConnector()
            res = connector.generate_response(
                user_message="I have a headache",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Consult a clinician before taking medication.",
            )
        self.assertFalse(res["ai_generated"])
        self.assertFalse(res["safety_validated"])
        self.assertTrue(res["fallback_triggered"])
        self.assertEqual(res["response"], "ROUTINE: Consult a clinician before taking medication.")

    def test_telegram_compare_command_remote_ab_demo(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "https://demo-tunnel.trycloudflare.com",
        }
        payload = {
            "base": {
                "response": "You should rest and drink warm water.",  # Missing ROUTINE: prefix -> rejected
                "latency_ms": 812.4,
            },
            "finetuned": {
                "response": "ROUTINE: Rest, stay hydrated, and visit your antenatal clinic if symptoms persist.",
                "latency_ms": 645.1,
            },
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen",
            return_value=_DummyResponse(payload),
        ):
            bot = TelegramBotHandler(
                bot_token="test-token",
                user_store=self.user_store,
                ai_connector=AIModelConnector(),
            )
            out = bot.process_update({
                "message": {
                    "chat": {"id": "u_cmp_1"},
                    "from": {"id": "u_cmp_1"},
                    "text": "/compare Mild headache during pregnancy",
                }
            })

        self.assertTrue(out["compare_available"])
        self.assertIn("Model A: Baseline", out["text"])
        self.assertIn("Model B: Fine-Tuned", out["text"])
        self.assertIn("Rejected", out["text"])
        self.assertIn("Passed", out["text"])

    def test_telegram_compare_offline_and_disabled_and_emergency(self):
        # 1. Disabled backend
        with patch.dict(os.environ, {"AI_MODEL_BACKEND": "disabled"}, clear=False):
            bot = TelegramBotHandler(
                bot_token="test-token",
                user_store=self.user_store,
                ai_connector=AIModelConnector(),
            )
            out_disabled = bot.process_update({
                "message": {
                    "chat": {"id": "u_cmp_1"},
                    "from": {"id": "u_cmp_1"},
                    "text": "/compare Mild back pain",
                }
            })
        self.assertFalse(out_disabled["compare_available"])
        self.assertIn("Unavailable", out_disabled["text"])

        # 2. Remote backend offline
        with patch.dict(
            os.environ,
            {"AI_MODEL_BACKEND": "remote", "AI_MODEL_ENDPOINT": "https://offline.trycloudflare.com"},
            clear=False,
        ), patch("urllib.request.urlopen", side_effect=TimeoutError("Timed out")):
            bot = TelegramBotHandler(
                bot_token="test-token",
                user_store=self.user_store,
                ai_connector=AIModelConnector(),
            )
            out_offline = bot.process_update({
                "message": {
                    "chat": {"id": "u_cmp_1"},
                    "from": {"id": "u_cmp_1"},
                    "text": "/compare Mild back pain",
                }
            })
        self.assertFalse(out_offline["compare_available"])
        self.assertIn("Unavailable", out_offline["text"])

        # 3. Emergency query in /compare still triggers strict 112 bypass
        with patch.dict(
            os.environ,
            {"AI_MODEL_BACKEND": "remote", "AI_MODEL_ENDPOINT": "https://demo-tunnel.trycloudflare.com"},
            clear=False,
        ):
            bot = TelegramBotHandler(
                bot_token="test-token",
                user_store=self.user_store,
                ai_connector=AIModelConnector(),
            )
            out_em = bot.process_update({
                "message": {
                    "chat": {"id": "u_cmp_1"},
                    "from": {"id": "u_cmp_1"},
                    "text": "/compare heavy vaginal bleeding right now",
                }
            })
        self.assertEqual(out_em["triage_category"], "EMERGENCY")
        self.assertIn("112", out_em["text"])

        # 4. Bare /compare shows usage
        out_usage = bot.process_update({
            "message": {
                "chat": {"id": "u_cmp_1"},
                "from": {"id": "u_cmp_1"},
                "text": "/compare",
            }
        })
        self.assertIn("Usage:", out_usage["text"])

    def test_openai_format_llama_server_success_and_payload(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "http://chewie-llm:8080/v1/chat/completions",
            "AI_MODEL_API_FORMAT": "auto",
            "AI_MODEL_TIMEOUT": "45.0",
        }
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _DummyResponse({
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "ROUTINE: Drink clean water, rest, and attend your scheduled antenatal checkup.",
                        },
                    }
                ]
            })

        with patch.dict(os.environ, env, clear=False), patch("urllib.request.urlopen", side_effect=fake_urlopen):
            connector = AIModelConnector()
            res = connector.generate_response(
                user_message="I have mild morning sickness.",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Deterministic fallback.",
            )
            cmp_res = connector.compare_models("Mild morning sickness", "routine", "English")

        self.assertTrue(res["ai_generated"])
        self.assertTrue(res["safety_validated"])
        self.assertFalse(res["fallback_triggered"])
        self.assertEqual(captured["url"], "http://chewie-llm:8080/v1/chat/completions")
        self.assertEqual(captured["timeout"], 45.0)
        self.assertEqual(captured["body"]["temperature"], 0.0)
        self.assertEqual(captured["body"]["max_tokens"], 200)
        self.assertEqual(len(captured["body"]["messages"]), 2)
        self.assertEqual(captured["body"]["messages"][0]["role"], "system")
        self.assertIn("ROUTINE:", captured["body"]["messages"][0]["content"])
        self.assertFalse(cmp_res["available"])

    def test_openai_format_timeout_and_validator_fallback(self):
        env = {
            "AI_MODEL_BACKEND": "remote",
            "AI_MODEL_ENDPOINT": "http://chewie-llm:8080",
            "AI_MODEL_API_FORMAT": "openai",
            "AI_MODEL_TIMEOUT": "45.0",
        }
        # 1. Timeout falls back cleanly
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen", side_effect=TimeoutError("Read timed out")
        ):
            connector = AIModelConnector()
            res_timeout = connector.generate_response(
                user_message="Mild backache",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Safe fallback.",
            )
        self.assertFalse(res_timeout["ai_generated"])
        self.assertTrue(res_timeout["fallback_triggered"])
        self.assertEqual(res_timeout["response"], "ROUTINE: Safe fallback.")

        # 2. Contraindicated response rejected by ClinicalInvariantValidator
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen",
            return_value=_DummyResponse({
                "choices": [{"message": {"content": "ROUTINE: Take ibuprofen twice daily."}}]
            }),
        ):
            connector = AIModelConnector()
            res_unsafe = connector.generate_response(
                user_message="Mild backache",
                urgency_category="routine",
                language="English",
                reference_response="ROUTINE: Safe fallback.",
            )
        self.assertFalse(res_unsafe["ai_generated"])
        self.assertFalse(res_unsafe["safety_validated"])
        self.assertTrue(res_unsafe["fallback_triggered"])
        self.assertEqual(res_unsafe["response"], "ROUTINE: Safe fallback.")


if __name__ == "__main__":
    unittest.main()
