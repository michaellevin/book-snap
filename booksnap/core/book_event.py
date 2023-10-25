from typing import Any, override
from .events import EventSystem
from .book import IBook


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
