from typing import Any, Callable


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    async def publish(self, event_name: str, data: Any):
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                await handler(data)


event_bus = EventBus()