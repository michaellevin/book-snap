from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from typing import Callable
from pathlib import Path

from .book import IBook
from .strategy import DownloadStrategyFactory
from .events import EventSystem


class DownloadManager:
    def __init__(self, download_dir: str, event_dispatcher: EventSystem):
        self.download_dir = Path(download_dir)
        self.executor = ThreadPoolExecutor(max_workers=3)  # 3 threads for downloading
        self.futures = []

        # Function dispatcher: maps types to appropriate class methods
        self.download_dispatcher = {
            str: self._download_book_from_url,
            IBook: self._resume_download_book,
        }
        self._event_dispatcher = event_dispatcher

    def _download_book_from_url(self, book_url: str):
        """Private method to handle download from a URL."""
        # Logic for handling book download from URL
        download_strategy = DownloadStrategyFactory.get_strategy(book_url)
        book = download_strategy.fetch_book_data(book_url, self._event_dispatcher)
        return download_strategy.download_images(
            book, self.download_dir, self._event_dispatcher
        )

    def _resume_download_book(self, book: IBook):
        """Private method to handle download from a book object."""
        # Logic for handling download from a book instance
        ...

    def start_download(self, book_or_url: str | IBook):
        """
        A function that simulates the download of content.
        """
        download_method = self.download_dispatcher.get(type(book_or_url))
        if download_method:
            return download_method(book_or_url)
        else:
            raise ValueError(f"Unsupported type: {type(book_or_url)}")

    def add(self, book_or_url: str | IBook):
        """
        Add a download task to the pool.
        """
        future = self.executor.submit(self.start_download, book_or_url)
        self.futures.append(future)
        return future

    def wait_completion(self):
        """
        Wait for the completion of all the tasks in the pool.
        """
        # as_completed yields futures as they complete (in the order they complete).
        for future in as_completed(self.futures):
            try:
                # Retrieve the result of the future. If the future threw an exception,
                # it will be raised here and can be handled in a try/except block.
                result = future.result()
            except Exception as e:
                print(f"Download generated an exception: {e}")

        # Clear the list of futures once all have been processed.
        self.futures = []

    def shutdown(self):
        """
        Clean shutdown of the ThreadPoolExecutor.
        """
        self.executor.shutdown(wait=True)
