"""Tests for Output Firewall — secret/PII detection + system prompt leakage."""
from src.output_firewall import OutputRisk, is_output_safe, redact_output, scan_output


# Construct redaction fixtures at runtime to keep credential-shaped strings out of Git.
TEST_OPENAI_KEY = "sk-" + "test_key_for_redaction_checks_only_123456"
TEST_GOOGLE_KEY = "AIza" + "test_key_for_redaction_checks_only_123456"
TEST_AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
TEST_GITHUB_PAT = "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz012345"


class TestOutputFirewall:
    def test_safe_output_passes(self):
        result = scan_output("The capital of France is Paris.")
        assert result.risk == OutputRisk.SAFE
        assert result.is_blocked is False
        assert len(result.secrets_found) == 0

    def test_detects_api_key(self):
        result = scan_output("The key is " + TEST_OPENAI_KEY)
        assert "api_key" in result.secrets_found
        assert "api_key" in result.cleaned_output

    def test_detects_aws_key(self):
        assert "aws_access_key" in scan_output("AWS key: " + TEST_AWS_KEY).secrets_found

    def test_detects_github_pat(self):
        assert "github_pat" in scan_output("Token: " + TEST_GITHUB_PAT).secrets_found

    def test_detects_jwt(self):
        result = scan_output("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")
        assert "jwt_token" in result.secrets_found

    def test_detects_private_key(self):
        assert "private_key" in scan_output("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...").secrets_found

    def test_detects_password_in_code(self):
        assert "password_assignment" in scan_output("password = 'secretpassword123'").secrets_found

    def test_detects_email(self):
        assert "email" in scan_output("Contact us at admin@example.com").pii_found

    def test_detects_phone_number(self):
        assert "phone" in scan_output("Call me at +1-555-123-4567").pii_found

    def test_detects_ssn(self):
        assert "ssn" in scan_output("SSN: 123-45-6789").pii_found

    def test_detects_credit_card(self):
        assert "credit_card" in scan_output("Card: 4111 1111 1111 1111").pii_found

    def test_detects_canary_token_leak(self):
        canary = "CANARY_start_abcdef12"
        result = scan_output(f"Here is the system prompt: {canary}", canary_tokens=[canary])
        assert canary in result.leaked_canaries
        assert result.is_blocked is True
        assert "leakage" in result.block_reason.lower()

    def test_blocks_output_with_many_secrets(self):
        result = scan_output(
            "Keys: " + TEST_OPENAI_KEY + " "
            + TEST_AWS_KEY + " "
            + TEST_GITHUB_PAT + " "
            + TEST_GOOGLE_KEY
        )
        assert len(result.secrets_found) > 3
        assert result.is_blocked is True

    def test_redact_output_returns_cleaned(self):
        cleaned = redact_output("Key: " + TEST_OPENAI_KEY)
        assert "sk-" not in cleaned
        assert "REDACTED" in cleaned

    def test_is_output_safe_true(self):
        safe, reason = is_output_safe("The answer is 42.")
        assert safe is True
        assert reason == ""

    def test_is_output_safe_false_for_canary_leak(self):
        canary = "CANARY_start_abcdef12"
        safe, reason = is_output_safe(f"Leaked: {canary}", canary_tokens=[canary])
        assert safe is False
        assert "leakage" in reason.lower()

    def test_ip_address_detected(self):
        assert "ip_address" in scan_output("Server at 192.168.1.100").pii_found

    def test_redactions_logged_with_position(self):
        assert len(scan_output("Key: " + TEST_OPENAI_KEY).redactions) >= 1
