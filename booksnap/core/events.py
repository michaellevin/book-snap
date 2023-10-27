from typing import Callable, Dict, List, Any


# * Observer pattern
class EventSystem:
    def __init__(self) -> None:
        self.listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def register_listener(
        self, event_name: str, callback: Callable[[Any], None]
    ) -> None:
        """Register a listener function to an event."""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def unregister_listener(
        self, event_name: str, callback: Callable[[Any], None]
    ) -> None:
        """Remove a listener function from an event."""
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)

    def emit(self, event_name: str, data: Any) -> None:
        """Trigger an event and call all listeners."""
        for callback in self.listeners.get(event_name, []):
            callback(data)
