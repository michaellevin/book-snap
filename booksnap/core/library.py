import os
import json
import threading
from pathlib import Path
from typing import List, Optional
from functools import partial
import tempfile
import logging
import traceback

from ._singleton import SingletonArgMeta
from .book import IBook
from .download_manager import DownloadManager
from .book_event import BookEventSystem
from .utils import hash_url
from .enums import BookState

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


class Library(metaclass=SingletonArgMeta):
    def __init__(self, books_dir: Optional[str]):
        self.root = Path(
            books_dir
            if os.path.exists(books_dir)
            else os.path.join(tempfile.TemporaryDirectory(), "BooksLibrary")
        )
        if not self.root.exists():
            self.root.mkdir(parents=True)

        self._metadata_file = self.root / ".metadata.json"
        if not self._metadata_file.exists():
            with open(self._metadata_file, "w") as f:
                json.dump({}, f)

        self._books = {}

        self._event_dispatcher = BookEventSystem()
        self._event_dispatcher.register_listener(
            "register_book", partial(self.store_book, final=False)
        )
        self._event_dispatcher.register_listener(
            "book_is_ready", partial(self.store_book, final=True)
        )

        self._download_manager = DownloadManager(self.root, self._event_dispatcher)

        self._metadata_lock = threading.Lock()

    def _ask_librarian(self, book_id: str) -> IBook | None:
        """Ask the librarian if the book is in the library."""
        self._books = self.load_metadata()
        book_data = self._books.get(book_id)
        if book_data is None:
            return None
        return IBook(**book_data)

    def get_book(self, book_url: str) -> IBook | None:
        """Get a book by its URL.

        If the book is already downloaded, return the book.
        If the book does not exist, initiate a download.
        If the book is in another state, handle according to the state.

        Returns:
            IBook if downloaded, None otherwise (with download initiated or in progress).
        """
        book_id = str(hash_url(book_url))
        book = self._ask_librarian(book_id)
        if book:
            logger.info(
                f"Book {book_id} is in the library, state: {BookState(book.state)}"
            )
            if book.state == BookState.PDF_READY.value:
                # Book is available and ready.
                return self.get_book_path(book)
            elif book.state == BookState.TERMINATED.value:
                # Resume book's download, it was downloaded before. (TODO)
                self._download_manager.add(book)
            elif book.state == BookState.DOWNLOADING.value:
                logging.warning("Book is downloading, please wait")
        else:
            # Book does not exist, so we initiate a download.
            future = self._download_manager.add(book_url)
            try:
                # Wait for the download task to complete and return the book.
                book = future.result()
                book.pprint()
                return self.get_book_path(book)
            except Exception as e:
                # Handle exceptions raised by the task (if any)
                logging.critical("An error occurred during download:")
                traceback.print_exc()
                # raise # Optionally, re-raise the exception
        return None

    def load_metadata(self) -> dict | None:
        if Path(self._metadata_file).exists():
            with open(self._metadata_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        return {}

    def store_book(self, book: IBook, final: bool = False) -> None:
        with self._metadata_lock:  # Use the lock while writing to the file
            metadata = self.load_metadata()
            metadata[str(book.id)] = book.to_dict(final)
            with open(self._metadata_file, "w", encoding="utf-8") as file:
                json.dump(metadata, file, ensure_ascii=False)

    def resume_all(self) -> List[int]:
        ...

    def get_books(self) -> List[dict]:
        """Get the list of books in the library."""
        ...
        # if self._books is None:
        #     self._books = self.load_metadata()
        # return self._books

    def get_book_path(self, book: IBook) -> Path:
        """Get the path to the book folder."""
        if book.state == BookState.PDF_READY.value:
            return self.root / (book.title + ".pdf")
        raise ValueError("Book is not ready yet")
