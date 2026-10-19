"""Format streamed agent, subagent, skill, and tool activity for the console."""

from contextlib import nullcontext
import json
from typing import Any


TOOL_ARGS_MAX_CHARS = 300
SUBAGENT_COLORS = {
    "quality-attribute-analyst": "magenta",
    "evidence-reviewer": "green",
    "general-purpose": "yellow",
}
ROOT_AGENT_LABEL = "ATAM coordinator"


def _tool_calls(node_update: Any) -> list[dict[str, Any]]:
    """Collect tool calls from a streamed node update without assuming message classes."""
    if not isinstance(node_update, dict):
        return []
    calls: list[dict[str, Any]] = []
    for message in node_update.get("messages", []):
        if isinstance(message, dict):
            calls.extend(message.get("tool_calls", []))
        else:
            calls.extend(getattr(message, "tool_calls", []))
    return calls


def format_tool_args(tool_call: dict[str, Any]) -> str:
    """Render compact arguments and truncate long values for readable console output."""
    rendered = json.dumps(tool_call.get("args", {}), ensure_ascii=False, separators=(",", ":"), default=str)
    if len(rendered) > TOOL_ARGS_MAX_CHARS:
        return f"{rendered[:TOOL_ARGS_MAX_CHARS].rstrip()}..."
    return rendered


def _display_progress(
    console: Any,
    status: Any,
    label: str,
    *,
    agent_name: str = ROOT_AGENT_LABEL,
    nested: bool = False,
    delegation: bool = False,
    tool_args: str | None = None,
) -> None:
    """Render one progress line, keeping argument styling independent of agent colors."""
    if status is not None:
        status.update(label)
    indentation = "  └─ " if nested else ""
    if console is None:
        marker = "Delegating:" if delegation else "Progress:"
        args_suffix = f" args: {tool_args}" if tool_args is not None else ""
        print(f"[{agent_name}] {indentation}{marker} {label}{args_suffix}")
        return
    from rich.markup import escape

    color = SUBAGENT_COLORS.get(agent_name, "cyan")
    agent_tag = f"[bold {color}]{escape(agent_name)}[/bold {color}]"
    marker = "[cyan]→[/cyan]" if delegation else "[dim]•[/dim]"
    args_suffix = f" [dim white]args: {escape(tool_args)}[/dim white]" if tool_args is not None else ""
    console.print(f"{agent_tag} {indentation}{marker} {escape(label)}{args_suffix}")


def _skill_file_label(tool_call: dict[str, Any]) -> tuple[str, str] | None:
    """Return a concise label for a read of a configured skill or reference."""
    if tool_call.get("name") != "read_file":
        return None
    args = tool_call.get("args", {})
    if not isinstance(args, dict):
        return None
    path = str(args.get("file_path", args.get("path", ""))).replace("\\", "/")
    parts = [part for part in path.split("/") if part]
    try:
        skills_index = parts.index("skills")
    except ValueError:
        return None
    skill_parts = parts[skills_index + 1 :]
    if len(skill_parts) < 2:
        return None
    skill_name = skill_parts[0]
    if skill_parts[1] == "SKILL.md":
        return "skill", skill_name
    if skill_parts[1] == "references":
        reference = "/".join(skill_parts[2:])
        return "reference", f"{skill_name}/{reference}" if reference else skill_name
    return None


def log_progress(console: Any, status: Any, event: dict[str, Any], state: dict[str, str]) -> None:
    """Show graph transitions, selected subagents, and requested skill files."""
    if event.get("type") != "updates":
        return
    namespace = event.get("ns", ())
    data = event.get("data", {})
    if not isinstance(data, dict):
        return

    current_agent = next(
        (name for part in namespace for name in SUBAGENT_COLORS if name in part),
        state.get("active_agent", ROOT_AGENT_LABEL),
    )
    for node, update in data.items():
        for call in _tool_calls(update):
            if call.get("name") == "task":
                args = call.get("args", {})
                subagent = args.get("subagent_type") if isinstance(args, dict) else None
                label = subagent or "subagent"
                if subagent in SUBAGENT_COLORS:
                    state["active_agent"] = subagent
                _display_progress(
                    console,
                    status,
                    label,
                    agent_name=subagent or current_agent,
                    delegation=True,
                    tool_args=format_tool_args(call),
                )
                continue

            skill_file = _skill_file_label(call)
            if skill_file is not None:
                kind, name = skill_file
                label = f"Load skill: {name}" if kind == "skill" else f"Read skill reference: {name}"
            else:
                label = f"Tool call: {call.get('name', 'unknown')}"
            _display_progress(
                console,
                status,
                label,
                agent_name=current_agent,
                nested=True,
                tool_args=format_tool_args(call),
            )

        # The parent tools node marks completion of its delegated subagent call.
        if node == "tools" and not namespace:
            state["active_agent"] = ROOT_AGENT_LABEL


def progress_context(verbose: bool) -> tuple[Any, Any]:
    """Return a Rich console and status context, with plain logging as a fallback."""
    if not verbose:
        return None, nullcontext()
    try:
        from rich.console import Console
    except ImportError:
        print("Progress: Rich is not installed; showing plain progress messages.")
        return None, nullcontext()
    console = Console(stderr=True)
    return console, console.status("Starting ATAM DeepAgents…", spinner="dots")
