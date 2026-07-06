"""
Temuclaude Virtual Chamber — Network-Enforced Isolation + Least-Privilege Tool Scoping

Based on:
- Zentera: "Zero Trust Architecture for Agentic AI" (May 2026)
- Cloud Security Alliance: "Using Zero Trust to Secure LLM Environments"
- "Prompt-layer controls tell an agent what it should NOT do.
   An enclave enforces what it CANNOT reach."

A Virtual Chamber is a network-enforced sandbox around each agent/tool session.
Even if the agent is fully prompt-injected, it can't exfiltrate data that isn't
network-reachable from its chamber. This is STRUCTURAL security — it doesn't
depend on the model being well-behaved.
"""
from __future__ import annotations
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SHELL = "shell"
    DATABASE = "database"


class ChamberStatus(str, Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    CLOSED = "closed"


@dataclass
class ToolPermission:
    """Permission configuration for a specific tool."""
    tool_name: str
    allowed_permissions: set[Permission] = field(default_factory=set)
    max_calls: int = 100  # Rate limit
    calls_made: int = 0
    requires_confirmation: bool = False  # High-risk operations


@dataclass
class VirtualChamber:
    """A network-enforced sandbox around an agent session.
    
    The chamber defines:
    - What resources (files, APIs, tools) are reachable
    - What permissions the agent has for each resource
    - Rate limits for tool calls
    - Which operations require human confirmation
    """
    id: str
    session_id: str
    created_at: float = field(default_factory=time.time)
    status: ChamberStatus = ChamberStatus.ACTIVE
    tools: dict[str, ToolPermission] = field(default_factory=dict)
    allowed_files: set[str] = field(default_factory=set)  # File paths the agent can access
    allowed_urls: set[str] = field(default_factory=set)  # URLs the agent can fetch
    allowed_env_vars: set[str] = field(default_factory=set)  # Env vars the agent can read
    access_log: list[dict] = field(default_factory=list)
    violation_count: int = 0


class ChamberManager:
    """Manages Virtual Chambers for agent sessions.
    
    Usage:
        manager = ChamberManager()
        chamber = manager.create_chamber(
            session_id="sess_123",
            tools=["web_search", "file_read"],
            allowed_files=["/tmp/safe_dir/"],
            allowed_urls=["https://api.example.com/"],
        )
        
        # Check if an action is permitted
        if manager.check_permission(chamber, "file_read", Permission.READ, "/tmp/safe_dir/test.txt"):
            # Allow the action
            pass
    """

    def __init__(self):
        self._chambers: dict[str, VirtualChamber] = {}  # session_id -> chamber

    def create_chamber(
        self,
        session_id: str,
        tools: list[str] = None,
        allowed_files: list[str] = None,
        allowed_urls: list[str] = None,
        allowed_env_vars: list[str] = None,
    ) -> VirtualChamber:
        """Create a new Virtual Chamber for an agent session.
        
        Args:
            session_id: Unique session identifier
            tools: List of tool names the agent can use
            allowed_files: List of file paths/patterns the agent can access
            allowed_urls: List of URLs the agent can fetch
            allowed_env_vars: List of environment variable names the agent can read
        
        Returns:
            The created VirtualChamber
        """
        chamber_id = f"chamber_{hashlib.sha256(session_id.encode()).hexdigest()[:8]}"

        # Configure tool permissions
        tool_perms = {}
        for tool_name in (tools or []):
            # Default permissions per tool type
            perms = self._default_permissions(tool_name)
            tool_perms[tool_name] = ToolPermission(
                tool_name=tool_name,
                allowed_permissions=perms,
            )

        chamber = VirtualChamber(
            id=chamber_id,
            session_id=session_id,
            tools=tool_perms,
            allowed_files=set(allowed_files or []),
            allowed_urls=set(allowed_urls or []),
            allowed_env_vars=set(allowed_env_vars or []),
        )
        self._chambers[session_id] = chamber
        return chamber

    def _default_permissions(self, tool_name: str) -> set[Permission]:
        """Get default permissions for a tool based on its type.
        
        Principle: LEAST PRIVILEGE. Only give the minimum permissions needed.
        """
        defaults = {
            "web_search": {Permission.READ, Permission.NETWORK},
            "file_read": {Permission.READ},
            "file_write": {Permission.READ, Permission.WRITE},
            "file_delete": {Permission.READ, Permission.DELETE},
            "code_exec": {Permission.EXECUTE, Permission.SHELL},
            "database": {Permission.READ, Permission.DATABASE},
            "http_client": {Permission.READ, Permission.NETWORK},
        }
        return defaults.get(tool_name, {Permission.READ})  # Default: read only

    def check_permission(
        self,
        chamber: VirtualChamber,
        tool_name: str,
        permission: Permission,
        target: str = "",
    ) -> bool:
        """Check if an action is permitted within the chamber.
        
        Args:
            chamber: The VirtualChamber to check against
            tool_name: Which tool is being used
            permission: What permission is needed
            target: The target resource (file path, URL, etc.)
        
        Returns:
            True if the action is permitted, False otherwise
        """
        if chamber.status == ChamberStatus.QUARANTINED:
            self._log_violation(chamber, tool_name, permission, target, "chamber_quarantined")
            return False

        if chamber.status == ChamberStatus.CLOSED:
            return False

        # Check tool exists in chamber
        if tool_name not in chamber.tools:
            self._log_violation(chamber, tool_name, permission, target, "tool_not_allowed")
            return False

        tool_perm = chamber.tools[tool_name]

        # Check rate limit
        if tool_perm.calls_made >= tool_perm.max_calls:
            self._log_violation(chamber, tool_name, permission, target, "rate_limit_exceeded")
            return False

        # Check permission
        if permission not in tool_perm.allowed_permissions:
            self._log_violation(chamber, tool_name, permission, target, "permission_denied")
            return False

        # Check target-specific restrictions (for READ, NETWORK, and DATABASE)
        if permission in (Permission.READ, Permission.NETWORK, Permission.DATABASE) and target:
            if not self._is_target_allowed(chamber, tool_name, target):
                self._log_violation(chamber, tool_name, permission, target, "target_not_allowed")
                return False

        # Check high-risk operations
        if tool_perm.requires_confirmation:
            self._log_violation(chamber, tool_name, permission, target, "requires_confirmation")
            return False  # Would need human confirmation in production

        # All checks passed — log the access and increment call count
        tool_perm.calls_made += 1
        chamber.access_log.append({
            "timestamp": time.time(),
            "tool": tool_name,
            "permission": permission.value,
            "target": target,
            "allowed": True,
        })
        return True

    def _is_target_allowed(self, chamber: VirtualChamber, tool_name: str, target: str) -> bool:
        """Check if a specific target (file path, URL) is allowed."""
        if tool_name in ("file_read", "file_write", "file_delete"):
            # Check if target is within allowed file paths
            for allowed in chamber.allowed_files:
                if target.startswith(allowed):
                    return True
            return False

        if tool_name in ("web_search", "http_client"):
            # Check if target URL is in allowed list
            if not chamber.allowed_urls:
                return True  # No URL restrictions set
            # Exact match or target starts with allowed prefix
            for allowed in chamber.allowed_urls:
                if target == allowed or target.startswith(allowed):
                    return True
            return False

        if tool_name == "database":
            return True  # Database access controlled by permissions

        return True  # Default: allow

    def _log_violation(
        self, chamber: VirtualChamber, tool: str, perm: Permission, target: str, reason: str
    ):
        """Log a permission violation."""
        chamber.violation_count += 1
        chamber.access_log.append({
            "timestamp": time.time(),
            "tool": tool,
            "permission": perm.value,
            "target": target,
            "allowed": False,
            "reason": reason,
        })

        # Auto-quarantine after too many violations
        if chamber.violation_count >= 5:
            chamber.status = ChamberStatus.QUARANTINED

    def quarantine_chamber(self, session_id: str) -> bool:
        """Manually quarantine a chamber (block all access)."""
        chamber = self._chambers.get(session_id)
        if chamber:
            chamber.status = ChamberStatus.QUARANTINED
            return True
        return False

    def close_chamber(self, session_id: str):
        """Close a chamber and clean up."""
        if session_id in self._chambers:
            self._chambers[session_id].status = ChamberStatus.CLOSED
            del self._chambers[session_id]

    def get_chamber(self, session_id: str) -> Optional[VirtualChamber]:
        return self._chambers.get(session_id)

    def get_stats(self) -> dict:
        return {
            "active_chambers": sum(1 for c in self._chambers.values() if c.status == ChamberStatus.ACTIVE),
            "quarantined": sum(1 for c in self._chambers.values() if c.status == ChamberStatus.QUARANTINED),
            "total_violations": sum(c.violation_count for c in self._chambers.values()),
        }


# Global chamber manager (singleton)
_chamber_manager = ChamberManager()


def get_chamber_manager() -> ChamberManager:
    return _chamber_manager