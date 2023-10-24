import os
import json
import threading
from pathlib import Path
from typing import List, Optional
from functools import partial
import tempfile
import logging
import traceback

from ._singleton import SingletonMeta, SingletonArgMeta
from .book import IBook
from .strategy import DownloadStrategyFactory
from .utils import hash_url
from .events import EventSystem
from .enums import BookState, OnlineLibrary
from .download_manager import DownloadManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


class LibraryMinistry(metaclass=SingletonMeta):
    def __init__(self):
        self._libraries = {}
        self.event_system = EventSystem()

    def build_library(self, books_dir: str):
        if self._libraries.get(books_dir) is None:
            self._libraries[books_dir] = Library(books_dir)
            logger.info(
                f"New Library is built! Please visit us: {books_dir}, 24/7 open"
            )
        return self._libraries[books_dir]

    def get_library(self, books_dir: str):
        library = self._libraries.get(books_dir)
        if library is None:
            raise ValueError(
                f"No library exists at {books_dir}"
            )  # or handle this some other appropriate way
        return library

    def get_all_libraries(self):
        return self._libraries


class Library(metaclass=SingletonArgMeta):
    def __init__(self, books_dir: Optional[str]):
        self.root = (
            books_dir
            if os.path.exists(books_dir)
            else os.path.join(tempfile.TemporaryDirectory(), "BooksLibrary")
        )
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        # print(self.root)

        self._metadata_file = os.path.join(self.root, ".metadata.json")
        if not os.path.exists(self._metadata_file):
            with open(self._metadata_file, "w") as f:
                json.dump({}, f)

        self._books = {}

        self._event_dispatcher = EventSystem()
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
            if book.state == BookState.READY.value:
                # Book is available and ready.
                return book
            elif book.state == BookState.TERMINATED.value:
                # Resume book's download, it was downloaded before.
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
                return book
            except Exception as e:
                # Handle exceptions raised by the task (if any)
                logging.critical("An error occurred during download:")
                traceback.print_exc()
                # raise # Optionally, re-raise the exception
        return None

    def load_metadata(self) -> None:
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
