"""DeepAgents adapter with lazy imports so core spec tooling stays lightweight."""

from .adapter import DeepAgentsRuntimeAdapter, create_deep_agent, execute_agent, execute_fan_out_fan_in

__all__ = ["DeepAgentsRuntimeAdapter", "create_deep_agent", "execute_agent", "execute_fan_out_fan_in"]
