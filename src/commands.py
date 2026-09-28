"""Registry of named actions that the backend API can trigger on the bot.

Each entry doubles as its own documentation: register a handler with a
description and its expected `params` keys, and it becomes discoverable via
GET /commands without needing separate docs to keep in sync.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

CommandHandler = Callable[[dict[str, Any]], Awaitable[Any]]


@dataclass
class CommandSpec:
    name: str
    handler: CommandHandler
    description: str = ""
    params: dict[str, str] = field(default_factory=dict)  # param name -> description


_COMMANDS: dict[str, CommandSpec] = {}


def register_command(
    name: str,
    *,
    description: str = "",
    params: dict[str, str] | None = None,
) -> Callable[[CommandHandler], CommandHandler]:
    """Decorator to register an async handler under a unique command name."""

    def decorator(func: CommandHandler) -> CommandHandler:
        if name in _COMMANDS:
            raise ValueError(f"Command '{name}' is already registered")
        _COMMANDS[name] = CommandSpec(name=name, handler=func, description=description, params=params or {})
        return func

    return decorator


def get_command(name: str) -> CommandHandler:
    spec = _COMMANDS.get(name)
    if spec is None:
        raise KeyError(name)
    return spec.handler


def available_commands() -> list[str]:
    return sorted(_COMMANDS.keys())


def describe_commands() -> list[dict[str, Any]]:
    """Full documentation payload: name, description and params per command."""
    return [
        {"name": spec.name, "description": spec.description, "params": spec.params}
        for spec in sorted(_COMMANDS.values(), key=lambda s: s.name)
    ]
