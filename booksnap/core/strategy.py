from abc import ABC, abstractmethod

from pathlib import Path
from urllib.request import urlopen
import json
import platform
import logging

logger = logging.getLogger(__name__)

from .enums import OnlineLibrary, Status
from .utils import system_call
from .events import EventSystem


class DownloadStrategy(ABC):
    def __init__(self):
        self.event_system = EventSystem()

    @abstractmethod
    def _fetch_data(self, book_url: str) -> dict:
        """Get the data of the book from the given URL."""
        pass

    @abstractmethod
    def download(self, book_url: str, dest_folder: str) -> None:
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

    def _fetch_data(self, book_url: str) -> dict:
        library_id = OnlineLibrary.PRLIB.value
        library_book_id = book_url.split("/")[-1]

        try:
            # logger.info("curl {}".format(book_url))
            output = system_call("curl {}".format(book_url))
        except RuntimeError as e:
            print("An error occurred:", e)
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
        # print(output)
        author = ""
        if "field_book_author" in output:
            author = (
                output.split('<a href="/search?f%5B0%5D=field_book_author')[1]
                .split(">")[1]
                .split("<")[0]
            )

        return {
            "url": book_url,
            "library_book_id": library_book_id,
            "library": library_id,
            "title": title,
            "author": author,
            "num_pages": len(all_images),
            "year": None,
            "_ids": ids,
            "_all_images": all_images,
        }

    def download(self, book_url: str, root_folder: str) -> None:
        """Logic for downloading a book from PrLib"""
        # * Fetch the book data
        book_tech_spec = self._fetch_data(book_url)

        # * Register the book in the library before downloading
        book_tech_spec["status"] = Status.DOWNLOADING.value
        book_tech_spec["progress_page"] = 0
        self.event_system.emit("register_book", book_tech_spec)

        # * Create the destination folder
        book_dest_folder = Path(root_folder, book_tech_spec["title"])
        book_dest_folder.mkdir(parents=True, exist_ok=True)

        # * Download fetched images
        # for i, im in enumerate(book_tech_spec["_all_images"]):
        #     im_address = self.SCAN_URL.format(*book_tech_spec["_ids"], im)
        #     logger.info(f"{i}/{book_tech_spec['num_pages']}  >  {im_address}")
        #     # Download the image
        #     system_call(
        #         "{} -l {} {}.jpeg".format(
        #             self.DEZOOMIFY_EXECUTABLE,
        #             im_address,
        #             str(book_dest_folder / str(i).zfill(3)),
        #         )
        #     )

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "prlib.ru" in book_url


class SPHLDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for SPHL.
    """

    def _fetch_data(self, book_url: str) -> dict:
        ...

    def download(self, book_url: str, dest_folder: str) -> None:
        # Logic for downloading a book from ELib
        pass

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
        for strategy in strategies:
            if strategy.can_handle_url(book_url):
                return strategy()

        raise ValueError(f"No available strategy for the URL: {book_url}")
