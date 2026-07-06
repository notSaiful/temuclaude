"""Tests for Virtual Chamber — network-enforced isolation + least-privilege."""
import pytest
from src.virtual_chamber import (
    ChamberManager, VirtualChamber, Permission, ChamberStatus,
    get_chamber_manager,
)


@pytest.fixture
def manager():
    return ChamberManager()


class TestVirtualChamber:
    def test_create_chamber(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_1",
            tools=["web_search", "file_read"],
        )
        assert chamber.id.startswith("chamber_")
        assert chamber.status == ChamberStatus.ACTIVE
        assert "web_search" in chamber.tools
        assert "file_read" in chamber.tools

    def test_check_permission_allowed(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_2",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        assert manager.check_permission(chamber, "file_read", Permission.READ, "/tmp/safe/test.txt") == True

    def test_check_permission_denied_wrong_tool(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_3",
            tools=["file_read"],
        )
        # Agent tries to use a tool not in its chamber
        assert manager.check_permission(chamber, "code_exec", Permission.EXECUTE, "/bin/bash") == False

    def test_check_permission_denied_file_outside_scope(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_4",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        # Agent tries to read a file outside its allowed directory
        assert manager.check_permission(chamber, "file_read", Permission.READ, "/etc/passwd") == False

    def test_check_permission_denied_delete_without_permission(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_5",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        # file_read only has READ permission, not DELETE
        assert manager.check_permission(chamber, "file_read", Permission.DELETE, "/tmp/safe/test.txt") == False

    def test_rate_limit_enforced(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_6",
            tools=["web_search"],
        )
        # Set a low rate limit
        chamber.tools["web_search"].max_calls = 3
        for _ in range(3):
            assert manager.check_permission(chamber, "web_search", Permission.NETWORK, "https://example.com") == True
        # 4th call should be denied
        assert manager.check_permission(chamber, "web_search", Permission.NETWORK, "https://example.com") == False

    def test_quarantine_blocks_all(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_7",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        manager.quarantine_chamber("test_session_7")
        assert chamber.status == ChamberStatus.QUARANTINED
        assert manager.check_permission(chamber, "file_read", Permission.READ, "/tmp/safe/test.txt") == False

    def test_auto_quarantine_after_violations(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_8",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        # Generate 5 violations
        for _ in range(5):
            manager.check_permission(chamber, "file_read", Permission.READ, "/etc/passwd")
        assert chamber.status == ChamberStatus.QUARANTINED

    def test_violation_count_increases(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_9",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        manager.check_permission(chamber, "file_read", Permission.READ, "/etc/passwd")
        manager.check_permission(chamber, "file_read", Permission.READ, "/etc/shadow")
        assert chamber.violation_count == 2

    def test_access_log_records_allowed_actions(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_10",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        manager.check_permission(chamber, "file_read", Permission.READ, "/tmp/safe/test.txt")
        assert len(chamber.access_log) == 1
        assert chamber.access_log[0]["allowed"] == True

    def test_access_log_records_violations(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_11",
            tools=["file_read"],
            allowed_files=["/tmp/safe/"],
        )
        manager.check_permission(chamber, "file_read", Permission.READ, "/etc/passwd")
        assert len(chamber.access_log) == 1
        assert chamber.access_log[0]["allowed"] == False
        assert "reason" in chamber.access_log[0]

    def test_close_chamber(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_12",
            tools=["file_read"],
        )
        manager.close_chamber("test_session_12")
        assert manager.get_chamber("test_session_12") is None

    def test_get_stats(self, manager):
        manager.create_chamber("test_session_13", tools=["web_search"])
        stats = manager.get_stats()
        assert stats["active_chambers"] >= 1

    def test_url_restriction_enforced(self, manager):
        chamber = manager.create_chamber(
            session_id="test_session_14",
            tools=["http_client"],
            allowed_urls=["https://api.example.com/"],
        )
        assert manager.check_permission(chamber, "http_client", Permission.NETWORK, "https://api.example.com/v1") == True
        assert manager.check_permission(chamber, "http_client", Permission.NETWORK, "https://evil.com/") == False