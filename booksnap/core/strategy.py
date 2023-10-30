from abc import ABC, abstractmethod

from pathlib import Path
from threading import Event
from typing import Optional
import requests
from bs4 import BeautifulSoup
import json
from time import sleep
import platform
import logging

logger = logging.getLogger(__name__)

from .enums import OnlineLibrary, BookState, EventType
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
        dest_folder: Path,
        event_dispatcher: EventSystem,
        start_page: Optional[int],
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

        # * Curl url to get the json data
        try:
            # logger.info("curl {}".format(book_url))
            output = system_call("curl {}".format(book_url))
            logger.info(f"Book data fetched from {book_url}")
            # pprint(output)
        except RuntimeError as err:
            logger.critical(err)
            return None

        # * Fetch title, author etc.
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

        # * Fetch technical json data (images, ids..)
        json_url = output.split('.json"')[0].split("https")[-1]
        json_cmd = f"https{json_url}.json".replace("\\", "")
        try:
            response = requests.get(json_cmd)
            # Check if the request was successful
            if response.status_code == 200:
                json_data = response.json()  # Assuming the response content is JSON
            else:
                logger.warning(
                    f"Failed to retrieve content, status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.critical(f"An error occurred: {e}")
            return None
        all_images = [dct["f"] for dct in json_data["pgs"]]
        ids = json_url.replace("\\", "").split("/")[-3:-1]
        # * Emit a book registration event to Library
        event_dispatcher.emit(
            EventType.REGISTER_BOOK,  # "register_book",
            book := IBook.create_instance(
                {
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
        start_page: int | None = 0,
        timeout: int = 0,
        main_event: Optional[Event] = None,
    ) -> IBook:
        """Logic for downloading a book from PrLib"""
        # * Create the destination folder
        book_dest_folder = root_folder / book.title
        book_dest_folder.mkdir(parents=True, exist_ok=True)

        # * Download fetched images
        if start_page is not None:
            ids = book.get_tech().ids
            all_images = book.get_tech().all_images
            len_all_images = len(all_images)
            for i in range(start_page, len_all_images):
                # Abort if main_event is set
                if main_event is not None and main_event.is_set():
                    logger.info("Download aborted")
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS, book, state=BookState.TERMINATED
                    )
                    return book

                # Construct the image path
                image_path = book_dest_folder / f"{str(i).zfill(4)}.jpeg"
                if image_path.exists():
                    image_path.unlink()  # Remove if exists

                # Download the image
                im_address = PrLibDownloadStrategy.SCAN_URL.format(*ids, all_images[i])
                try:
                    system_call(
                        f"{PrLibDownloadStrategy.DEZOOMIFY_EXECUTABLE} -l {im_address} {str(image_path)}"
                    )
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS,
                        book,
                        state=BookState.DOWNLOADING,
                        progress_page=i + 1,
                    )
                    logger.info(
                        f"page:{i+1}/{book.num_pages}  |  url: {im_address} downloaded succesfully"
                    )
                    # Pause if necessary
                    if timeout:
                        sleep(timeout)
                except RuntimeError as err:
                    logger.critical(err)
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS, book, state=BookState.TERMINATED
                    )

            event_dispatcher.emit(
                EventType.IMAGES_DOWNLOADED, book, state=BookState.DOWNLOAD_FINISHED
            )

        # * Convert images to PDF
        # sleep(5)
        try:
            create_pdf(book_dest_folder, book.title)
            event_dispatcher.emit(
                EventType.BOOK_IS_READY, book, state=BookState.PDF_READY
            )
        except RuntimeError as err:
            logger.critical(err)
            event_dispatcher.emit(
                EventType.IMAGES_DOWNLOADED, book, state=BookState.TERMINATED
            )

        return book

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "prlib.ru" in book_url


class SPHLDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for SPHL.
    """

    SCAN_URL = "http://elib.shpl.ru/pages/{}/zooms/6"

    def parse_html_for_key(
        html_doc: str, key: str, is_title: bool = False
    ) -> str | None:
        soup = BeautifulSoup(html_doc, "html.parser")
        tag_with_key = soup.find("td", text=key)
        clean_value = None
        if tag_with_key:
            value_for_key = tag_with_key.find_next_sibling("td").get_text(strip=True)
            clean_value = value_for_key.split("(")[0].strip()
        elif is_title:
            clean_value = soup.title.string if soup.title else None
        return clean_value

    def fetch_book_data(book_url: str, event_dispatcher: EventSystem) -> dict:
        library_id = OnlineLibrary.PRLIB.value
        library_book_id = book_url.split("/")[-1]

        # Read html doc
        # html_doc = system_call(f"curl {book_url}")
        response = requests.get(book_url)
        response.raise_for_status()
        html_doc = response.text

        # Parse it
        title = SPHLDownloadStrategy.parse_html_for_key(html_doc, key="Заглавие")
        if title is None:
            title = library_book_id
        author = SPHLDownloadStrategy.parse_html_for_key(html_doc, key="Автор")
        year = SPHLDownloadStrategy.parse_html_for_key(html_doc, "Год издания")
        # print(title, author, year)
        ids = str(html_doc).split('links_z0":{')[1].split("}")[0]
        ids = eval("{" + ids + "}")
        list_of_ids = list(ids.keys())

        # Emit signal
        event_dispatcher.emit(
            EventType.REGISTER_BOOK,  # "register_book",
            book := IBook.create_instance(
                {
                    "url": book_url,
                    "library_book_id": library_book_id,
                    "library": library_id,
                    "title": title,
                    "author": author,
                    "num_pages": len(list_of_ids),
                    "year": year,
                    "state": BookState.REGISTERED.value,
                    "_tech_dict": {"image_ids": list_of_ids},
                }
            ),
        )
        return book

    def download_images(
        book: IBook,
        root_folder: str,
        event_dispatcher: EventSystem,
        start_page: int = 0,
        timeout: int = 90,
        main_event: Optional[Event] = None,
    ) -> IBook:
        # Logic for downloading a book from ELib
        book_dest_folder = root_folder / book.title
        book_dest_folder.mkdir(parents=True, exist_ok=True)

        if start_page is not None:
            image_ids = book.get_tech().image_ids
            len_ids = len(image_ids)
            for i in range(start_page, len_ids):
                # Abort if main_event is set
                if main_event is not None and main_event.is_set():
                    logger.info("Download aborted")
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS, book, state=BookState.TERMINATED
                    )
                    return book

                # Pause
                sleep(timeout)

                # Construct the image path
                image_path = book_dest_folder / f"{str(i).zfill(4)}.jpeg"
                if image_path.exists():
                    image_path.unlink()  # Remove if exists

                # Download the image
                im = image_ids[i]
                im_address = SPHLDownloadStrategy.SCAN_URL.format(im)
                try:
                    im_cmd = f'curl {im_address} -o "{str(image_path)}"'
                    logging.info(im_cmd)
                    system_call(im_cmd)
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS,
                        book,
                        state=BookState.DOWNLOADING,
                        progress_page=i + 1,
                    )
                    logger.info(
                        f"page:{i+1}/{book.num_pages}  |  url: {im_address} downloaded succesfully"
                    )

                except RuntimeError as err:
                    logger.critical(err)
                    event_dispatcher.emit(
                        EventType.UPDATE_BOOK_PROGRESS, book, state=BookState.TERMINATED
                    )

            event_dispatcher.emit(
                EventType.IMAGES_DOWNLOADED, book, state=BookState.DOWNLOAD_FINISHED
            )

        # * Convert images to PDF
        # sleep(5)
        try:
            create_pdf(book_dest_folder, book.title)
            event_dispatcher.emit(
                EventType.BOOK_IS_READY, book, state=BookState.PDF_READY
            )
        except RuntimeError as err:
            logger.critical(err)
            event_dispatcher.emit(
                EventType.IMAGES_DOWNLOADED, book, state=BookState.TERMINATED
            )

        return book

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
