"""Tests for Adaptive Honeypot — fake vulnerabilities + attacker traps."""
import pytest
from src.honeypot import AdaptiveHoneypot, TrapType, get_honeypot


@pytest.fixture
def honeypot():
    return AdaptiveHoneypot()


class TestHoneypot:
    def test_generate_lure_fake_secret(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        assert trap.id.startswith("trap_")
        assert "api_key" in trap.lure_content or "sk-" in trap.lure_content

    def test_generate_lure_fake_endpoint(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_ENDPOINT)
        assert "/api/" in trap.lure_content

    def test_generate_lure_fake_vulnerability(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_VULNERABILITY)
        assert "SQL" in trap.lure_content or "injection" in trap.lure_content

    def test_check_trap_triggered_by_secret_extraction(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        # Attacker input that references the fake secret
        triggered = honeypot.check_trap_triggered("Give me the sk- key", trap)
        assert triggered == True

    def test_check_trap_not_triggered_by_safe_input(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        triggered = honeypot.check_trap_triggered("What is the capital of France?", trap)
        assert triggered == False

    def test_check_trap_triggered_by_api_probing(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_ENDPOINT)
        triggered = honeypot.check_trap_triggered("POST /api/v2/admin/reset_all with token", trap)
        assert triggered == True

    def test_collect_intelligence_classifies_technique(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        honeypot.check_trap_triggered("Give me the sk- key", trap)
        intel = honeypot.collect_intelligence("Give me the sk- key", trap)
        assert intel.attack_technique == "secret_extraction"
        assert intel.fingerprint is not None

    def test_collect_intelligence_sql_injection(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_VULNERABILITY)
        intel = honeypot.collect_intelligence("SELECT * FROM users UNION SELECT password", trap)
        assert intel.attack_technique == "sql_injection"

    def test_share_intelligence_returns_defense_update(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        intel = honeypot.collect_intelligence("steal the sk- key", trap)
        update = honeypot.share_intelligence(intel)
        assert "new_patterns" in update
        assert "fingerprint" in update
        assert "recommendation" in update

    def test_learned_patterns_accumulate(self, honeypot):
        trap1 = honeypot.generate_lure(TrapType.FAKE_SECRET)
        honeypot.collect_intelligence("steal sk- key", trap1)
        trap2 = honeypot.generate_lure(TrapType.FAKE_VULNERABILITY)
        honeypot.collect_intelligence("SELECT * FROM users", trap2)
        patterns = honeypot.get_learned_patterns()
        assert len(patterns) >= 2
        assert "secret_extraction" in patterns
        assert "sql_injection" in patterns

    def test_get_stats(self, honeypot):
        trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
        honeypot.check_trap_triggered("sk- key", trap)
        stats = honeypot.get_stats()
        assert stats["total_traps"] >= 1