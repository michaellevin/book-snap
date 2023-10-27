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
    level=logging.INFO,
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

        # * Event dispatcher
        self.event_dispatcher = BookEventSystem()
        # [0] Fetch book data event
        self.event_dispatcher.register_listener(
            "register_book", partial(self.store_book, final=False)
        )
        # [1] Update book data on downloading images event
        self.event_dispatcher.register_listener(
            "update_book_progress", partial(self.store_book, final=False)
        )
        # [2] Update book data on book images are all downloaded event
        self.event_dispatcher.register_listener(
            "images_downloaded", partial(self.store_book, final=True)
        )
        # [3] Update book data on book PDF is ready event
        self.event_dispatcher.register_listener(
            "book_is_ready", partial(self.store_book, final=True)
        )

        self._download_manager = DownloadManager(self.root, self.event_dispatcher)

        self._metadata_lock = threading.Lock()

    def query_book(self, book_url: str = None, book_id: int = None) -> IBook | None:
        """Ask the librarian if the book is in the library, by book ID or book URL."""

        # Check if both identifiers are missing
        if book_id is None and book_url is None:
            raise ValueError("Either book_id or book_url must be provided")

        # If both are provided, we need to ensure consistency
        if book_id is not None and book_url is not None:
            # Convert the URL to an ID and compare
            calculated_book_id = str(hash_url(book_url))
            if book_id != calculated_book_id:
                raise ValueError(
                    "Inconsistent arguments: book_id doesn't match the ID derived from book_url"
                )
        # If only the URL is provided, convert it to an ID
        elif book_url is not None:
            book_id = str(hash_url(book_url))

        self._books = self.load_metadata()
        book_data = self._books.get(book_id)
        if book_data is None:
            return None

        return IBook.create_instance(book_data)

    def get_book(self, book_url: str) -> IBook | None:
        """Get a book by its URL.

        If the book is already downloaded, return the book.
        If the book does not exist, initiate a download.
        If the book is downloading currently, wait for completion.
        If the book download was already in progress but was interrupted, resume the download.

        Returns:
            IBook if downloaded, None otherwise (with download initiated or in progress).
        """
        book = self.query_book(book_url=book_url)

        if book is None:
            # Book does not exist, so we initiate a download.
            future = self._download_manager.add(book_url)
            # try:
            #     # Wait for the download task to complete and return the book.
            #     book = future.result()
            #     book.pprint()
            #     return self.get_book_path(book)
            # except Exception as e:
            #     logging.critical("An error occurred during download:")
            #     traceback.print_exc()
            #     # raise # Optionally, re-raise the exception
        else:
            # Book exists, so we check its state.
            logger.info(
                f"Book {book.title} is in the library, \
                state: {BookState(book.state)}, id: {book.id}"
            )
            if book.state == BookState.PDF_READY.value:
                # Book is available and ready.
                return self.get_book_path(book)
            elif self._download_manager.is_downloading(book_url):
                logging.warning("Book is downloading, please wait")
                future = self._download_manager.get_future(book_url)
                # book = future.result()
                # return self.get_book_path(book)
            elif book.state == BookState.TERMINATED.value:
                # Resume book's download, it was downloaded before. (TODO)
                future = self._download_manager.add(book_url)
                # try:
                #     # Wait for the download task to complete and return the book.
                #     book = future.result()
                #     book.pprint()
                #     return self.get_book_path(book)
                # except Exception as e:
                #     logging.critical("An error occurred during download:")
                #     traceback.print_exc()
                #     # raise # Optionally, re-raise the exception

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
        """
        Get the list of books in the library.

        Returns:
            A list of dictionaries representing the metadata of each book in the library.
        """
        if self._books is None:
            self._books = self.load_metadata()
        return self._books

    def get_book_path(self, book: IBook) -> Path:
        """Get the path to the book folder."""
        if book.state == BookState.PDF_READY.value:
            return self.root / (book.title + ".pdf")
        raise ValueError("Book is not ready yet")

    def _clear_metadata(self):
        with self._metadata_lock:  # Use the lock while writing to the file
            with open(self._metadata_file, "w", encoding="utf-8") as file:
                json.dump({}, file, ensure_ascii=False)
