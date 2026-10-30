"""Internal integrity helpers shared by benchmark recorders."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    """Hash a file incrementally so large predictions do not fill memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    """Hash an already serialized artifact without reading it again."""
    return hashlib.sha256(value).hexdigest()


def contains_secret_setting(value: Any) -> bool:
    """Detect credential-like names and common secret formats before recording settings."""
    secret_fragments = (
        "api_key", "access_key", "private_key", "client_key", "authorization",
        "cookie", "secret", "password", "credential", "token", "bearer",
    )
    secret_value_patterns = (
        # Common provider/API token prefixes, including OpenAI, GitHub, Slack, and AWS.
        re.compile(r"(?i)(?:sk-(?:proj-)?|gh[pousr]_|github_pat_|xox[baprs]-|AKIA)[A-Za-z0-9_-]{12,}"),
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    )
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")
            if (
                any(fragment in normalized for fragment in secret_fragments)
                or contains_secret_setting(nested)
            ):
                return True
    elif isinstance(value, (list, tuple)):
        return any(contains_secret_setting(item) for item in value)
    elif isinstance(value, str):
        return any(pattern.search(value) for pattern in secret_value_patterns)
    return False
