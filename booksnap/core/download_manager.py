from threading import Event
from concurrent.futures import ThreadPoolExecutor, Future, as_completed, wait
from typing import Callable
from pathlib import Path
import traceback
from logging import getLogger

logger = getLogger(__name__)

from .book import IBook
from .strategy import DownloadStrategyFactory
from .events import EventSystem
from .enums import BookState


# PEP 604 typing: Path | str
class DownloadManager:
    def __init__(self, download_dir: Path | str, event_dispatcher: EventSystem):
        # A directory where the downloaded books will be stored
        self.download_dir = self._prepare_download_dir(download_dir)

        # ThreadPoolExecutor. 3 threads for downloading
        self.executor = ThreadPoolExecutor(max_workers=3)

        # This event is used to interrupt the main thread
        self.main_event = Event()

        # Future objects for each download task
        self.futures = []

        # A dictionary of active downloads: {url: Future}
        self.active_downloads = {}

        # Function dispatcher: maps types to appropriate class methods
        self._download_dispatcher = {
            str: self._download_book_from_url,
            IBook: self._resume_download_book,
        }

        # Event dispatcher
        self._event_dispatcher = event_dispatcher

    @staticmethod
    def _prepare_download_dir(download_dir: Path | str) -> Path:
        """
        ~ Duck-typing
        Prepares the download directory by creating it if it doesn't exist and checking that it is a directory.

        Args:
            download_dir (Path or str): The path to the download directory.

        Returns:
            Path: The Path object representing the download directory.

        Raises:
            TypeError: If download_dir is not a Path or a string.
            ValueError: If the path exists but is not a directory or cannot be accessed.
        """
        if not isinstance(download_dir, (Path, str)):
            raise TypeError("Download directory must be a Path or string.")
        path = Path(download_dir)
        if not path.exists():
            path.mkdir(
                parents=True, exist_ok=True
            )  # This creates the directory if it doesn't exist. Handle exceptions as necessary.
        elif not path.is_dir():
            raise ValueError(
                f"The path {path} is not a directory or cannot be accessed."
            )
        return path

    def _download_book_from_url(self, book_url: str) -> IBook:
        """Private method to handle download from a URL."""
        # Logic for handling book download from URL
        download_strategy = DownloadStrategyFactory.get_strategy(book_url)
        book = download_strategy.fetch_book_data(book_url, self._event_dispatcher)
        return download_strategy.download_images(
            book=book,
            root_folder=self.download_dir,
            event_dispatcher=self._event_dispatcher,
            main_event=self.main_event,
        )

    def _resume_download_book(self, book: IBook) -> IBook:
        """Private method to handle download from a book object."""
        # Logic for handling download from a book instance
        download_strategy = DownloadStrategyFactory.get_strategy(book.url)
        return download_strategy.download_images(
            book=book,
            root_folder=self.download_dir,
            event_dispatcher=self._event_dispatcher,
            start_page=book.progress_page,
        )

    def _start_download(self, book_or_url: str | IBook) -> None:
        """
        A function that simulates the download of content.
        """
        download_method = self._download_dispatcher.get(type(book_or_url))
        if download_method:
            return download_method(book_or_url)
        else:
            raise ValueError(f"Unsupported type: {type(book_or_url)}")

    def add(self, book_or_url: str | IBook) -> Future:
        """
        Add a download task to the pool.
        """
        self.main_event.clear()
        future = self.executor.submit(self._start_download, book_or_url)
        self.futures.append(future)
        url = book_or_url.url if isinstance(book_or_url, IBook) else book_or_url
        self.active_downloads[url] = future
        # future.add_done_callback(self.on_download_finished)
        return future

    # def on_download_finished(self, future: Future) -> None:
    #     try:
    #         book = future.result()
    #     except Exception as e:
    #         logger.critical("An error occurred during download:")
    #         traceback.print_exc()

    def get_future(self, book_url: str) -> Future:
        """
        Get the future associated with the book URL.
        """
        return self.active_downloads[book_url]

    def wait_completion(self) -> None:
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

    def is_downloading(self, book_url: str) -> bool:
        """
        Check if the book is currently being downloaded.
        """
        if book_url in self.active_downloads:
            # If the future is still running, the book is being downloaded
            return not self.active_downloads[book_url].done()

        return False

    def shutdown(self, wait: bool = False) -> None:
        """
        Clean shutdown of the ThreadPoolExecutor.
        """
        self.executor.shutdown(wait=wait)
        # event_dispatcher.emit("book_is_ready", book, state=BookState.TERMINATED)

    def abort(self, book_url: str) -> None:
        """
        Interrupt the download of the book.
        """
        try:
            # Cancel the future
            future = self.active_downloads[book_url]
            if not future.running():
                logger.warning("Future is not running, cancelling")
                future.cancel()
            else:
                logger.warning("Future is running, cancelling the next iteration step.")
                self.main_event.set()

            # Remove the future from the list of active downloads
            del self.active_downloads[book_url]

            logger.warning(f"Cancelled: {book_url}")
        except (KeyError, RuntimeError) as e:
            logger.warning(f"Book {book_url} is not being downloaded.")
