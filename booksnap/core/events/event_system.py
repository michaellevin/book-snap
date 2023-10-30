from typing import Dict, Any
from .signal import Signal


# * Observer pattern
class EventSystem:
    def __init__(self) -> None:
        self.signals: Dict = {}

    def register_signal(self, event_id: int) -> Signal:
        self.signals[event_id] = Signal(event_id)
        return self.signals[event_id]

    def unregister_signal(self, event_id: int) -> None:
        """Remove a signal from an event."""
        if event_id in self.signals:
            del self.signals[event_id]

    def emit(self, event_id: int, data: Any) -> None:
        """Trigger an event and call all listeners."""
        if event_id in self.signals:
            self.signals[event_id].emit(data)
