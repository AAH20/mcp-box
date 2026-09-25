"""
Curated MCP Package Registry.
Defines installable MCP server descriptors, execution commands, and secret bindings.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class McpPackage:
    name: str
    description: str
    command: str
    args: List[str]
    required_secrets: List[str] = field(default_factory=list)
    default_env: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "args": self.args,
            "required_secrets": self.required_secrets,
            "default_env": self.default_env,
        }


class McpPackageRegistry:
    """
    Registry of verified community and enterprise MCP servers.
    """

    CATALOG: Dict[str, McpPackage] = {
        "postgres": McpPackage(
            name="postgres",
            description="Read/write PostgreSQL database access via MCP",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            required_secrets=["POSTGRES_CONNECTION_STRING"],
        ),
        "filesystem": McpPackage(
            name="filesystem",
            description="Secure local filesystem access with path whitelisting",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/Users/shared"],
            required_secrets=[],
        ),
        "github": McpPackage(
            name="github",
            description="GitHub repos, issues, pull requests, and commit exploration",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            required_secrets=["GITHUB_PERSONAL_ACCESS_TOKEN"],
        ),
        "slack": McpPackage(
            name="slack",
            description="Slack channel messaging and message history query",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-slack"],
            required_secrets=["SLACK_BOT_TOKEN"],
        ),
        "sqlite": McpPackage(
            name="sqlite",
            description="Local SQLite database query and schema exploration",
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", "./app.db"],
            required_secrets=[],
        ),
        "brave-search": McpPackage(
            name="brave-search",
            description="Web and local search queries via Brave Search API",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            required_secrets=["BRAVE_API_KEY"],
        ),
    }

    @classmethod
    def get_package(cls, name: str) -> Optional[McpPackage]:
        return cls.CATALOG.get(name.lower())

    @classmethod
    def list_packages(cls) -> List[McpPackage]:
        return list(cls.CATALOG.values())
