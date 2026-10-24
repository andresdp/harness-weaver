"""Filesystem boundaries shared by the ATAM coordinator and its specialists."""


def atam_filesystem_permissions() -> list[object]:
    """Limit agents to reading ATAM skills while denying all filesystem writes."""
    try:
        from deepagents import FilesystemPermission
    except ImportError as exc:
        raise RuntimeError("DeepAgents is required to configure ATAM filesystem access") from exc

    return [
        # Agents need the on-demand skill tree, but not reports from earlier runs.
        FilesystemPermission(operations=["read"], paths=["/skills/**"], mode="allow"),
        FilesystemPermission(operations=["read"], paths=["/**", "/"], mode="deny"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]
