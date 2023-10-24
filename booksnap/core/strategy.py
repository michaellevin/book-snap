from abc import ABC, abstractmethod

from pathlib import Path
from urllib.request import urlopen
import json
from time import sleep
import platform
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from .enums import OnlineLibrary, BookState
from .utils import system_call, create_pdf
from .events import EventSystem
from .book import IBook


class DownloadStrategy(ABC):
    @staticmethod
    @abstractmethod
    def fetch_book_data(book_url: str, event_dispatcher: EventSystem) -> dict:
        """Get the data of the book from the given URL."""
        pass

    @staticmethod
    @abstractmethod
    def download_images(
        book: IBook,
        dest_folder: str,
        event_dispatcher: EventSystem,
        timeout: Optional[int],
    ) -> IBook:
        """Download the book from the given URL."""
        pass

    @staticmethod
    @abstractmethod
    def can_handle_url(book_url: str) -> bool:
        """Check if the strategy can handle the given URL."""
        pass


class PrLibDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for PrLib.
    """

    SCAN_URL = "https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF=/var/data/scans/public/{}/{}/{}&JTL=2,0&CVT=JPEG"
    DEZOOMIFY_EXECUTABLE = f"bin/{platform.system().lower()}/dezoomify-rs"

    def fetch_book_data(book_url: str, event_dispatcher: EventSystem) -> dict:
        library_id = OnlineLibrary.PRLIB.value
        library_book_id = book_url.split("/")[-1]

        try:
            # logger.info("curl {}".format(book_url))
            output = system_call("curl {}".format(book_url))
        except RuntimeError as err:
            logger.critical(err)
            return None

        js = output.split('.json"')[0].split("https")[-1]
        js_cmd = f"https{js}.json".replace("\\", "")
        j = urlopen(js_cmd)
        # pprint(output)
        data = json.load(j)
        all_images = [dct["f"] for dct in data["pgs"]]
        ids = js.replace("\\", "").split("/")[-3:-1]
        # pprint(all_images)
        title = (
            output.split('<meta itemprop="name" content="')[1]
            .split('"')[0]
            .replace(" ", "_")
        )
        author = ""
        if "field_book_author" in output:
            author = (
                output.split('<a href="/search?f%5B0%5D=field_book_author')[1]
                .split(">")[1]
                .split("<")[0]
            )
        # emit a book registration event to Library
        event_dispatcher.emit(
            "register_book",
            book := IBook(
                **{
                    "url": book_url,
                    "library_book_id": library_book_id,
                    "library": library_id,
                    "title": title,
                    "author": author,
                    "num_pages": len(all_images),
                    "year": None,
                    "state": BookState.REGISTERED.value,
                    "_tech_dict": {
                        "ids": ids,
                        "all_images": all_images,
                    },
                }
            ),
        )
        return book

    def download_images(
        book: IBook,
        root_folder: Path,
        event_dispatcher: EventSystem,
        timeout: int = 0,
    ) -> IBook:
        """Logic for downloading a book from PrLib"""
        # * Create the destination folder
        book_dest_folder = root_folder / book.title
        book_dest_folder.mkdir(parents=True, exist_ok=True)

        # * Update status
        event_dispatcher.emit(
            "register_book", book, state=BookState.DOWNLOADING, progress_page=-1
        )
        # * Download fetched images
        ids = book.get_tech().ids
        all_images = book.get_tech().all_images
        for i, im in enumerate(all_images):
            im_address = PrLibDownloadStrategy.SCAN_URL.format(*ids, im)
            logger.info(f"page:{i+1}/{book.num_pages}  |  url: {im_address}")
            image_path = book_dest_folder / f"{str(i).zfill(4)}.jpeg"
            if image_path.exists():
                image_path.unlink()  # Remove if exists
            # Download the image
            try:
                system_call(
                    f"{PrLibDownloadStrategy.DEZOOMIFY_EXECUTABLE} -l {im_address} {str(image_path)}"
                )
                book.set_progress_page(i)
                event_dispatcher.emit("register_book", book, progress_page=i + 1)
                if timeout:
                    sleep(timeout)  # Pause for 1 second
            except RuntimeError as err:
                logger.critical(err)
                event_dispatcher.emit("register_book", book, state=BookState.TERMINATED)

        event_dispatcher.emit("book_is_ready", book, state=BookState.DOWNLOAD_FINISHED)
        # * Convert images to PDF
        create_pdf(book_dest_folder, book.title)
        event_dispatcher.emit("book_is_ready", book, state=BookState.PDF_READY)
        return book

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "prlib.ru" in book_url


class SPHLDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for SPHL.
    """

    def fetch_book_data(self, book_url: str, event_dispatcher: EventSystem) -> dict:
        ...

    def download_images(
        self,
        book: IBook,
        dest_folder: str,
        event_dispatcher: EventSystem,
        timeout: int = 90,
    ) -> IBook:
        # Logic for downloading a book from ELib
        return 0

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "elib.shpl.ru" in book_url


class DownloadStrategyFactory:
    @staticmethod
    def get_strategy(book_url: str) -> DownloadStrategy:
        """Get the appropriate download strategy for the given URL."""
        # List all possible strategies here
        strategies = [
            PrLibDownloadStrategy,
            SPHLDownloadStrategy,
        ]  # Add more as you implement them

        # Select the appropriate strategy based on the URL
        # Using the walrus operator (:=) introduced in PEP 572 for concise assignment within expressions.
        if any((strategy := s).can_handle_url(book_url) for s in strategies):
            return strategy

        raise ValueError(f"No available strategy for the URL: {book_url}")
