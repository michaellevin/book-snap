import os
import json
import threading
from pathlib import Path
from typing import List
import tempfile
import logging
from .strategy import DownloadStrategyFactory
from ._singleton import SingletonMeta

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)


class Library(metaclass=SingletonMeta):
    def __init__(self, books_dir: str):
        self.books_dir = (
            books_dir
            if os.path.exists(books_dir)
            else os.path.join(tempfile.TemporaryDirectory(), "BooksLibrary")
        )
        if not os.path.exists(self.books_dir):
            os.makedirs(self.books_dir)
        print(self.books_dir)
        self._metadata_file = os.path.join(self.books_dir, ".metadata.json")
        if not os.path.exists(self._metadata_file):
            with open(self._metadata_file, "w") as f:
                json.dump({}, f)
        self._download_strategy = None
        self._books = None
        self._metadata_lock = threading.Lock()

    def download_book(self, book_url: str, resume: bool = False) -> int:
        """Download a book using a strategy appropriate for the given URL."""
        try:
            self._download_strategy = DownloadStrategyFactory.get_strategy(book_url)
            return self._download_strategy.download(book_url)
        except:
            logging.exception("Failed to download the book")
            return -1

    def get_books(self) -> List[dict]:
        """Get the list of books in the library."""
        if self._books is None:
            self._books = self.load_metadata()
        return self._books

    def load_metadata(self) -> None:
        with self.metadata_lock:  # Use the lock while reading the file
            if Path(self.metadata_file).exists():
                with open(self.metadata_file, "r") as file:
                    data = json.load(file)
                return data
            return {}

    def save_metadata(self, book) -> None:
        with self.metadata_lock:  # Use the lock while writing to the file
            data = self.load_metadata()
            data[book.library_id] = book.to_dict()
            with open(self.metadata_file, "w") as file:
                json.dump(data, file)

    def update_download_status(self, book_id: int, status: str) -> None:
        ...

    def resume_all(self) -> List[int]:
        ...
