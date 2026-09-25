"""
Comprehensive Unit Tests for mcp-box.
Tests vault encryption/decryption, package catalog, universal client syncing, and environment resolution.
"""

from __future__ import annotations
import json
import os
import shutil
import tempfile
import unittest
from mcp_box.registry import McpPackageRegistry
from mcp_box.supervisor import McpSupervisor
from mcp_box.synchronizer import UniversalClientSynchronizer
from mcp_box.vault import EncryptedSecretVault


class TestMcpBox(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vault = EncryptedSecretVault(vault_dir=self.temp_dir)
        self.syncer = UniversalClientSynchronizer(self.vault)
        self.supervisor = McpSupervisor(self.vault)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vault_encryption_and_persistence(self):
        self.vault.set_secret("DATABASE_URL", "postgres://user:super_secret@localhost:5432/db")
        self.assertTrue(self.vault.has_secret("DATABASE_URL"))
        self.assertEqual(self.vault.get_secret("DATABASE_URL"), "postgres://user:super_secret@localhost:5432/db")

        # Verify ciphertext on disk
        with open(self.vault.vault_file, "r") as f:
            raw = json.load(f)
        self.assertNotIn("super_secret", raw["DATABASE_URL"])

        # Re-load vault instance from disk
        reloaded = EncryptedSecretVault(vault_dir=self.temp_dir)
        self.assertEqual(reloaded.get_secret("DATABASE_URL"), "postgres://user:super_secret@localhost:5432/db")

    def test_package_registry_catalog(self):
        packages = McpPackageRegistry.list_packages()
        self.assertGreaterEqual(len(packages), 5)
        pg = McpPackageRegistry.get_package("postgres")
        self.assertIsNotNone(pg)
        self.assertIn("POSTGRES_CONNECTION_STRING", pg.required_secrets)

    def test_universal_client_synchronization(self):
        self.vault.set_secret("POSTGRES_CONNECTION_STRING", "mock_pg_url")
        pkgs = [McpPackageRegistry.get_package("postgres")]

        # Test shim mode
        cfg_shim = self.syncer.generate_client_config(pkgs, inject_vault_shim=True)
        self.assertIn("postgres", cfg_shim["mcpServers"])
        self.assertEqual(cfg_shim["mcpServers"]["postgres"]["command"], "mcp-box")
        self.assertEqual(cfg_shim["mcpServers"]["postgres"]["args"], ["run", "postgres"])

        # Test direct injection mode
        cfg_direct = self.syncer.generate_client_config(pkgs, inject_vault_shim=False)
        self.assertEqual(cfg_direct["mcpServers"]["postgres"]["env"]["POSTGRES_CONNECTION_STRING"], "mock_pg_url")

    def test_supervisor_environment_resolution(self):
        self.vault.set_secret("POSTGRES_CONNECTION_STRING", "resolved_secret_token")
        pg = McpPackageRegistry.get_package("postgres")
        env = self.supervisor.resolve_environment(pg)
        self.assertEqual(env["POSTGRES_CONNECTION_STRING"], "resolved_secret_token")


if __name__ == "__main__":
    unittest.main()
