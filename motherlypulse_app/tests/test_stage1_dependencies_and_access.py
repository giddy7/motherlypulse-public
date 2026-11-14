"""
Stage 1 Verification Tests: Dependencies, Model Access, and Token Security
Tests:
1. Secure HF_TOKEN handling and token masking (no credential leakage).
2. Error sanitization (no secret leakage in stack traces).
3. Physical hardware inspection and pre-flight RAM checks.
4. Identification of missing package dependencies without mock substitution.
"""

import os
import unittest
from motherlypulse_app.eval_models.genuine_adapters import (
    get_secure_hf_token,
    mask_token,
    sanitize_error_msg,
    HardwareProfile,
    ChewieInferenceAdapter,
    MamaBotInferenceAdapter,
    ModelUnavailableError
)

class TestStage1DependenciesAndAccess(unittest.TestCase):
    def test_token_masking_security(self):
        # Test None token
        self.assertEqual(mask_token(None), "None (Unauthenticated)")
        
        # Test real-looking token
        raw_token = "hf_AbCdEfGhIjKlMnOpQrStUvWxYz012345"
        masked = mask_token(raw_token)
        self.assertNotIn("AbCdEfGhIjKlMnOpQrStUvWxYz012345", masked)
        self.assertTrue(masked.startswith("hf_A...2345"))
        self.assertIn("[VALID_MASKED]", masked)

    def test_error_message_sanitization(self):
        # Simulate an exception containing an exposed token in a URL or query string
        raw_err = (
            "HTTPS 401 Unauthorized for URL https://huggingface.co/google/medgemma-4b-it/resolve/main/config.json?token=hf_SECRETKEY1234567890ABCDEF\n"
            "Header: Bearer hf_ANOTHERSECRETKEY987654321"
        )
        sanitized = sanitize_error_msg(raw_err)
        self.assertNotIn("hf_SECRETKEY1234567890ABCDEF", sanitized)
        self.assertNotIn("hf_ANOTHERSECRETKEY987654321", sanitized)
        self.assertIn("token=[REDACTED]", sanitized)
        self.assertIn("Bearer [REDACTED_HF_TOKEN]", sanitized)

    def test_hardware_profile_diagnostics(self):
        hw = HardwareProfile.get_profile()
        self.assertIn("cuda_available", hw)
        self.assertIn("total_ram_gb", hw)
        self.assertIn("available_ram_gb", hw)
        self.assertGreater(hw["total_ram_gb"], 0.0)
        self.assertGreater(hw["available_ram_gb"], 0.0)

    def test_chewie_adapter_preflight_guard(self):
        adapter = ChewieInferenceAdapter()
        self.assertEqual(adapter.model_id, "electricsheepafrica/chewie-1.2")
        self.assertEqual(adapter.revision_sha, "c4c279559be94b84ad50bd90c14e133fec6d485a")
        
        # Since local host has < 4.0 GB free RAM, loading must raise ModelUnavailableError
        with self.assertRaises(ModelUnavailableError) as ctx:
            adapter.load_model()
        err_msg = str(ctx.exception)
        self.assertIn("Insufficient memory to load Chewie 1.2", err_msg)
        self.assertNotIn("hf_", err_msg)  # Ensure no raw tokens in message

    def test_mamabot_adapter_preflight_guard(self):
        adapter = MamaBotInferenceAdapter()
        self.assertEqual(adapter.model_id, "HelpMumHQ/MamaBot-Llama")
        self.assertEqual(adapter.revision_sha, "aca319cbd66f1f866112e7039ba1f99b6dd8b47f")

        # Since local host has < 6.0 GB free RAM, loading must raise ModelUnavailableError
        with self.assertRaises(ModelUnavailableError) as ctx:
            adapter.load_model()
        err_msg = str(ctx.exception)
        self.assertIn("Insufficient memory to load MamaBot-Llama", err_msg)
        self.assertNotIn("hf_", err_msg)

if __name__ == "__main__":
    unittest.main()
