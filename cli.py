"""
Command Line Interface for mcp-box.
Manage packages, encrypt credentials, and synchronize AI agent configs.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from mcp_box.registry import McpPackageRegistry
from mcp_box.synchronizer import UniversalClientSynchronizer
from mcp_box.vault import EncryptedSecretVault


def run_demo(outdir: str):
    os.makedirs(outdir, exist_ok=True)
    vault = EncryptedSecretVault(vault_dir=os.path.join(outdir, "vault"))
    syncer = UniversalClientSynchronizer(vault)

    print("\n" + "=" * 80)
    print("📦 MCP-BOX: UNIVERSAL PACKAGE MANAGER & ENCRYPTED VAULT FOR MCP")
    print("=" * 80)

    # 1. Inspect Registry
    print("\n[Step 1] Browsing Curated MCP Package Catalog...")
    packages = McpPackageRegistry.list_packages()
    for p in packages:
        secrets_str = f"(Requires: {', '.join(p.required_secrets)})" if p.required_secrets else "(Zero Secrets)"
        print(f"   • {p.name:15} | {p.description[:45]:45} {secrets_str}")

    # 2. Encrypt Credentials in Vault
    print("\n[Step 2] Storing Encrypted Credentials in Local Vault (Zero Plaintext)...")
    vault.set_secret("POSTGRES_CONNECTION_STRING", "postgresql://admin:super_secret_password_99@db.prod.internal:5432/finance")
    vault.set_secret("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_live_token_for_agentic_automation_9988")
    vault.set_secret("SLACK_BOT_TOKEN", "xoxb-998877665544-mock-slack-token")

    print(f"   Encrypted Secret Keys in Vault: {vault.list_keys()}")
    print(f"   Vault File on Disk: {vault.vault_file} (Ciphertext Blob)")

    # 3. Synchronize Across Clients
    print("\n[Step 3] Universal Multi-Client Configuration Synchronization...")
    selected_pkgs = [
        McpPackageRegistry.get_package("postgres"),
        McpPackageRegistry.get_package("github"),
        McpPackageRegistry.get_package("filesystem"),
    ]

    claude_cfg = os.path.join(outdir, "claude_desktop_config.json")
    cursor_cfg = os.path.join(outdir, "cursor_mcp.json")

    # Secure shim mode (secrets remain locked in vault)
    syncer.sync_to_file(claude_cfg, selected_pkgs, inject_vault_shim=True)
    syncer.sync_to_file(cursor_cfg, selected_pkgs, inject_vault_shim=False)

    print(f"   ✅ Claude Desktop Config: {claude_cfg} (Protected by mcp-box vault shim)")
    print(f"   ✅ Cursor IDE Config:     {cursor_cfg} (Direct injection mode)")

    # Display sample generated config
    with open(claude_cfg, "r") as f:
        print("\n--- Generated Claude Desktop Config Sample ---")
        print(f.read())

    print("=" * 80)
    print("✅ MCP-Box demo completed successfully.")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="mcp-box: Universal MCP Package Manager & Vault")
    subparsers = parser.add_subparsers(dest="command")

    demo_p = subparsers.add_parser("demo", help="Run end-to-end mcp-box demo")
    demo_p.add_argument("--outdir", default="./output_mcpbox", help="Output directory")

    list_p = subparsers.add_parser("list", help="List available MCP packages")

    vault_p = subparsers.add_parser("vault", help="Manage encrypted vault secrets")
    vault_p.add_argument("action", choices=["set", "get", "list"])
    vault_p.add_argument("key", nargs="?", help="Secret key name")
    vault_p.add_argument("value", nargs="?", help="Secret value (for set)")

    args = parser.parse_args()

    if not args.command or args.command == "demo":
        run_demo(getattr(args, "outdir", "./output_mcpbox"))
    elif args.command == "list":
        for p in McpPackageRegistry.list_packages():
            print(f"{p.name:15} - {p.description}")
    elif args.command == "vault":
        vault = EncryptedSecretVault()
        if args.action == "set" and args.key and args.value:
            vault.set_secret(args.key, args.value)
            print(f"✅ Secret '{args.key}' encrypted and saved.")
        elif args.action == "get" and args.key:
            val = vault.get_secret(args.key)
            print(f"{args.key} = {val if val else '[NOT FOUND]'}")
        elif args.action == "list":
            print("Vault Keys:", vault.list_keys())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
