import os
import json
import threading
from pathlib import Path
from typing import List
import tempfile
import logging

from ._singleton import SingletonMeta, SingletonArgMeta
from .book import IBook
from .strategy import DownloadStrategyFactory
from .utils import generate_id_from_url
from .events import EventSystem

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
    def __init__(self, books_dir: str):
        self.root = (
            books_dir
            if os.path.exists(books_dir)
            else os.path.join(tempfile.TemporaryDirectory(), "BooksLibrary")
        )
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        print(self.root)
        self._metadata_file = os.path.join(self.root, ".metadata.json")
        if not os.path.exists(self._metadata_file):
            with open(self._metadata_file, "w") as f:
                json.dump({}, f)
        self._books = None
        self._metadata_lock = threading.Lock()

    def download_book(self, book_url: str, resume: bool = False) -> int:
        """Download a book using a strategy appropriate for the given URL."""
        # Check if book is already downloaded
        if self._books is None:
            self._books = self.load_metadata()
        # book_id = generate_id_from_url(book_url)
        ...

        try:
            download_strategy = DownloadStrategyFactory.get_strategy(book_url)
            download_strategy.event_system.register_listener(
                "register_book", self.register_book
            )
            return download_strategy.download(book_url, self.root)
        except:
            logging.exception("Failed to download the book")
            return -1

    def register_book(self, book_tech_spec: dict) -> None:
        """Register a book in the library."""
        new_book = IBook(
            url=book_tech_spec["url"],
            library_book_id=book_tech_spec["library_book_id"],
            library=book_tech_spec["library"],
            title=book_tech_spec["title"],
            author=book_tech_spec["author"],
            num_pages=book_tech_spec["num_pages"],
            year=book_tech_spec["year"],
            status=book_tech_spec["status"],
            progress_page=book_tech_spec["progress_page"],
        )
        # self._books[new_book.id] = new_book
        # print(new_book)
        self.save_metadata(new_book)

    def update_book(self, new_data: dict) -> None:
        ...

    def get_book(self, book_url: str) -> IBook:
        """Get a book by its url."""
        book_id = generate_id_from_url(book_url)
        self._books = self.load_metadata()
        return IBook(**self._books[str(book_id)])

    def get_books(self) -> List[dict]:
        """Get the list of books in the library."""
        if self._books is None:
            self._books = self.load_metadata()
        return self._books

    def load_metadata(self) -> None:
        if Path(self._metadata_file).exists():
            with open(self._metadata_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        return {}

    def save_metadata(self, book) -> None:
        with self._metadata_lock:  # Use the lock while writing to the file
            data = self.load_metadata()
            data[book.id] = book.to_dict()
            with open(self._metadata_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False)

    def update_download_status(self, book_id: int, status: str) -> None:
        ...

    def resume_all(self) -> List[int]:
        ...
