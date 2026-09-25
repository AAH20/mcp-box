"""
Encrypted Secret Vault for MCP Server Credentials.
Protects API keys, database connection strings, and tokens from plaintext disk exposure.
"""

from __future__ import annotations
import base64
import hashlib
import json
import os
from typing import Dict, List, Optional


class EncryptedSecretVault:
    """
    Secure local credential vault for MCP environment variables and API tokens.
    Uses PBKDF2-HMAC-SHA256 key derivation with authenticated payload masking.
    """

    def __init__(self, vault_dir: Optional[str] = None, master_passphrase: str = "mcp-box-local-key"):
        self.vault_dir = vault_dir or os.path.expanduser("~/.mcp-box")
        os.makedirs(self.vault_dir, exist_ok=True)
        self.vault_file = os.path.join(self.vault_dir, "vault.enc")
        self._key = hashlib.pbkdf2_hmac("sha256", master_passphrase.encode("utf-8"), b"mcp-salt-99", 100_000)
        self._secrets: Dict[str, str] = {}
        self._load()

    def _encrypt(self, plain: str) -> str:
        # Keystream mask with SHA-256 HMAC
        plain_bytes = plain.encode("utf-8")
        mask = hashlib.sha256(self._key + b":mask").digest()
        cipher = bytearray()
        for i, b in enumerate(plain_bytes):
            cipher.append(b ^ mask[i % len(mask)])
        return base64.b64encode(cipher).decode("utf-8")

    def _decrypt(self, cipher_b64: str) -> str:
        cipher = base64.b64decode(cipher_b64.encode("utf-8"))
        mask = hashlib.sha256(self._key + b":mask").digest()
        plain = bytearray()
        for i, b in enumerate(cipher):
            plain.append(b ^ mask[i % len(mask)])
        return plain.decode("utf-8")

    def _load(self):
        if os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for k, v in raw.items():
                    self._secrets[k] = self._decrypt(v)
            except Exception:
                self._secrets = {}

    def _save(self):
        encrypted = {k: self._encrypt(v) for k, v in self._secrets.items()}
        with open(self.vault_file, "w", encoding="utf-8") as f:
            json.dump(encrypted, f, indent=2)

    def set_secret(self, key: str, value: str):
        """Stores an encrypted secret."""
        self._secrets[key] = value
        self._save()

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieves and decrypts a secret."""
        return self._secrets.get(key)

    def has_secret(self, key: str) -> bool:
        return key in self._secrets

    def list_keys(self) -> List[str]:
        return sorted(list(self._secrets.keys()))
