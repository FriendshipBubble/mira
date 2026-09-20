"""Registry of named actions that the backend API can trigger on the bot.

Each entry doubles as its own documentation: register a handler with a
description and its expected `params` keys, and it becomes discoverable via
GET /commands without needing separate docs to keep in sync.
"""

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

CommandHandler = Callable[[Dict[str, Any]], Awaitable[Any]]


@dataclass
class CommandSpec:
    name: str
    handler: CommandHandler
    description: str = ""
    params: Dict[str, str] = field(default_factory=dict)  # param name -> description


_COMMANDS: Dict[str, CommandSpec] = {}


def register_command(
    name: str,
    *,
    description: str = "",
    params: Optional[Dict[str, str]] = None,
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


def available_commands() -> List[str]:
    return sorted(_COMMANDS.keys())


def describe_commands() -> List[Dict[str, Any]]:
    """Full documentation payload: name, description and params per command."""
    return [
        {"name": spec.name, "description": spec.description, "params": spec.params}
        for spec in sorted(_COMMANDS.values(), key=lambda s: s.name)
    ]
