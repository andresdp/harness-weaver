"""DeepAgents adapter with lazy imports so core spec tooling stays lightweight."""

from .adapter import DeepAgentsRuntimeAdapter, create_deep_agent, execute_agent

__all__ = ["DeepAgentsRuntimeAdapter", "create_deep_agent", "execute_agent"]
