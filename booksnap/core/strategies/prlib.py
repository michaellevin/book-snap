import platform
from pathlib import Path
from time import sleep
from typing import Optional, override
from threading import Event
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

from ._strategy import DownloadStrategy
from ..events import BookEventSystem
from ..book import IBook, BookState
from ..enums import OnlineLibrary, EventType
from ..utils import system_call


class PrLibStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for PrLib.
    """

    SCAN_URL = "https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF=/var/data/scans/public/{}/{}/{}&JTL=2,0&CVT=JPEG"
    DEZOOMIFY_EXECUTABLE = f"bin/{platform.system().lower()}/dezoomify-rs"

    @override  # PEP 698
    def fetch_book_data(book_url: str, event_dispatcher: BookEventSystem) -> dict:
        library_id = OnlineLibrary.PRLIB.value
        library_book_id = book_url.split("/")[-1]

        # * Curl url to get the json data
        html_doc = DownloadStrategy.get_html_doc(book_url)
        if html_doc is None:
            return None

        # * Fetch title, author etc.
        soup = BeautifulSoup(html_doc, "html.parser")

        title = ""
        title_line = soup.find("meta", itemprop="name")
        if title_line:
            title = title_line.get("content", "").strip().replace(" ", "_")

        author = ""
        author_field = soup.find(
            "a", href=True, attrs={"href": lambda x: x and "field_book_author" in x}
        )
        if author_field:
            author = author_field.text.strip()

        # * Fetch technical json data (images, ids..)
        json_url = html_doc.split('.json"')[0].split("https")[-1]
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
            EventType.REGISTER_BOOK,
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

    @override  # PEP 698
    def download_images(
        book: IBook,
        root_folder: Path,
        event_dispatcher: BookEventSystem,
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
                im_address = PrLibStrategy.SCAN_URL.format(*ids, all_images[i])
                try:
                    system_call(
                        f'{PrLibStrategy.DEZOOMIFY_EXECUTABLE} -l {im_address} "{str(image_path)}"'
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
        DownloadStrategy.create_pdf(book_dest_folder, book, event_dispatcher)

        return book

    @override
    def can_handle_url(book_url: str) -> bool:
        return "prlib.ru" in book_url
