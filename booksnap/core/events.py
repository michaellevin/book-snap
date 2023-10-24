from typing import Callable, Dict, List, Any, override
from .book import IBook


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


class BookEventSystem(EventSystem):
    @override  # PEP 698
    def emit(self, event_name: str, book: IBook, **kwargs: Any) -> None:
        """Trigger a Book event and call all listeners."""
        state = kwargs.get("state")
        if state is not None:
            book.set_state(state.value)  # Assuming 'state' has a 'value' attribute
        progress_page = kwargs.get("progress_page")
        if progress_page is not None:
            book.set_progress_page(progress_page)
        super().emit(event_name, book)
