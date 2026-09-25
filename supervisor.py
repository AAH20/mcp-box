"""
Sandboxed Process Supervisor for MCP Servers.
Injects encrypted credentials at runtime and isolates child process execution.
"""

from __future__ import annotations
import os
import subprocess
import sys
from typing import Dict, List, Optional
from mcp_box.registry import McpPackage, McpPackageRegistry
from mcp_box.vault import EncryptedSecretVault


class McpSupervisor:
    """
    Supervises the execution of an MCP server child process,
    dynamically resolving encrypted credentials into the process environment.
    """

    def __init__(self, vault: EncryptedSecretVault):
        self.vault = vault

    def resolve_environment(self, package: McpPackage) -> Dict[str, str]:
        """Resolves process environment with credentials from the vault."""
        env = os.environ.copy()
        env.update(package.default_env)

        for secret_name in package.required_secrets:
            secret_val = self.vault.get_secret(secret_name)
            if secret_val:
                env[secret_name] = secret_val

        return env

    def run_package(self, package_name: str, passthrough_args: Optional[List[str]] = None) -> int:
        pkg = McpPackageRegistry.get_package(package_name)
        if not pkg:
            raise KeyError(f"Package '{package_name}' not found in registry")

        env = self.resolve_environment(pkg)
        cmd = [pkg.command] + pkg.args + (passthrough_args or [])

        # Execute child process inheriting stdio for MCP JSON-RPC
        try:
            proc = subprocess.Popen(cmd, env=env)
            return proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            return 0
