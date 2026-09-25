"""
Universal Client Synchronizer.
Generates and writes configuration files for Claude Desktop, Cursor, Windsurf, and Google AX.
"""

from __future__ import annotations
import json
import os
from typing import Dict, List, Optional
from mcp_box.registry import McpPackage
from mcp_box.vault import EncryptedSecretVault


class UniversalClientSynchronizer:
    """
    Synchronizes installed MCP servers and encrypted credentials across multiple AI agent clients.
    """

    def __init__(self, vault: EncryptedSecretVault):
        self.vault = vault

    def generate_client_config(
        self,
        packages: List[McpPackage],
        inject_vault_shim: bool = True,
    ) -> Dict[str, Any]:
        """
        Generates standard mcpServers schema.
        If inject_vault_shim is True, routes execution through mcp-box supervisor to preserve secret encryption.
        """
        mcp_servers: Dict[str, Any] = {}

        for pkg in packages:
            env_vars: Dict[str, str] = pkg.default_env.copy()
            for secret_key in pkg.required_secrets:
                val = self.vault.get_secret(secret_key)
                if val:
                    env_vars[secret_key] = val
                else:
                    env_vars[secret_key] = f"__VAULT_SECRET_UNSET_{secret_key}__"

            if inject_vault_shim:
                # Secure shim execution
                mcp_servers[pkg.name] = {
                    "command": "mcp-box",
                    "args": ["run", pkg.name],
                    "env": {},  # Secrets remain inside encrypted vault
                }
            else:
                mcp_servers[pkg.name] = {
                    "command": pkg.command,
                    "args": pkg.args,
                    "env": env_vars,
                }

        return {"mcpServers": mcp_servers}

    def sync_to_file(self, target_path: str, packages: List[McpPackage], inject_vault_shim: bool = False) -> str:
        """Writes configuration to target client path."""
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        config = self.generate_client_config(packages, inject_vault_shim=inject_vault_shim)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return target_path
