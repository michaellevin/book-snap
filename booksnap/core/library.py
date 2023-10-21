import os
import json
from typing import List
import tempfile


class Library:
    def __init__(self, books_dir: str):
        self.books_dir = (
            books_dir
            if os.path.exists(books_dir)
            else os.path.join(tempfile.TemporaryDirectory(), "BooksLibrary")
        )
        print(self.books_dir)
        if not os.path.exists(self.books_dir):
            os.makedirs(self.books_dir)
        self.metadata_dir = os.path.join(self.books_dir, "metadata")
        self.download_statuses = (
            {}
        )  # Consider initializing from a file if the data is persistent.

    def load_metadata(self) -> None:
        """Load metadata from the metadata directory and populate the library."""
        # Here, you'd iterate over all files in the metadata directory,
        # read each one, and create an IBook instance (or some other relevant object)
        # for each one, storing it in a suitable data structure.

    def save_metadata(self, book) -> None:
        """Save metadata for a single book to its metadata file."""
        # Convert the book's metadata to a dictionary, then to a JSON string,
        # and save it to a file named after the book in the metadata directory.

    def update_download_status(self, book_id: int, status: str) -> None:
        """Update the download status of the given book to the given status."""
        # Update the status in both the in-memory data structure and the book's metadata file.

    def get_books_to_download(self) -> List[int]:
        """Retrieve a list of book IDs for books that need to be downloaded."""
        # This could be as simple as filtering the in-memory list of books for ones with certain statuses.

    # ... (other methods like add_book, remove_book, etc. would need to consider file operations too)
