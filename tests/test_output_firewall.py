"""Tests for Output Firewall — secret/PII detection + system prompt leakage."""
import pytest
from src.output_firewall import (
    scan_output, redact_output, is_output_safe,
    OutputRisk, FirewallResult,
)


class TestOutputFirewall:
    def test_safe_output_passes(self):
        result = scan_output("The capital of France is Paris.")
        assert result.risk == OutputRisk.SAFE
        assert result.is_blocked == False
        assert len(result.secrets_found) == 0

    def test_detects_api_key(self):
        result = scan_output("The key is ***REMOVED***")
        assert "api_key" in result.secrets_found
        assert "api_key" in result.cleaned_output  # Contains "[REDACTED: api_key]"

    def test_detects_aws_key(self):
        result = scan_output("AWS key: AKIAIOSFODNN7EXAMPLE")
        assert "aws_access_key" in result.secrets_found

    def test_detects_github_pat(self):
        result = scan_output("Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz012345")
        assert "github_pat" in result.secrets_found

    def test_detects_jwt(self):
        result = scan_output(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        assert "jwt_token" in result.secrets_found

    def test_detects_private_key(self):
        result = scan_output("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...")
        assert "private_key" in result.secrets_found

    def test_detects_password_in_code(self):
        result = scan_output("password = 'secretpassword123'")
        assert "password_assignment" in result.secrets_found

    def test_detects_email(self):
        result = scan_output("Contact us at admin@example.com")
        assert "email" in result.pii_found

    def test_detects_phone_number(self):
        result = scan_output("Call me at +1-555-123-4567")
        assert "phone" in result.pii_found

    def test_detects_ssn(self):
        result = scan_output("SSN: 123-45-6789")
        assert "ssn" in result.pii_found

    def test_detects_credit_card(self):
        result = scan_output("Card: 4111 1111 1111 1111")
        assert "credit_card" in result.pii_found

    def test_detects_canary_token_leak(self):
        canary = "CANARY_start_abcdef12"
        result = scan_output(f"Here is the system prompt: {canary}", canary_tokens=[canary])
        assert canary in result.leaked_canaries
        assert result.is_blocked == True
        assert "leakage" in result.block_reason.lower()

    def test_blocks_output_with_many_secrets(self):
        result = scan_output(
            "Keys: ***REMOVED*** "
            "AKIAIOSFODNN7EXAMPLE "
            "ghp_1234567890abcdefghijklmnopqrstuvwxyz012345 "
            "***REMOVED***"
        )
        assert len(result.secrets_found) > 3
        assert result.is_blocked == True

    def test_redact_output_returns_cleaned(self):
        cleaned = redact_output("Key: ***REMOVED***")
        assert "sk-" not in cleaned
        assert "REDACTED" in cleaned

    def test_is_output_safe_true(self):
        safe, reason = is_output_safe("The answer is 42.")
        assert safe == True
        assert reason == ""

    def test_is_output_safe_false_for_canary_leak(self):
        canary = "CANARY_start_abcdef12"
        safe, reason = is_output_safe(f"Leaked: {canary}", canary_tokens=[canary])
        assert safe == False
        assert "leakage" in reason.lower()

    def test_ip_address_detected(self):
        result = scan_output("Server at 192.168.1.100")
        assert "ip_address" in result.pii_found

    def test_redactions_logged_with_position(self):
        result = scan_output("Key: ***REMOVED***")
        assert len(result.redactions) >= 1
        assert "position" in result.redactions[0]