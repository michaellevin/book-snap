import platform
from pathlib import Path
from time import sleep
from typing import Optional, override
from threading import Event

# import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

from ._strategy import DownloadStrategy
from ..events import BookEventSystem
from ..book import IBook, BookState
from ..enums import OnlineLibrary, EventType

# from ..utils import system_call


class SphlStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for SPHL.
    """

    SCAN_URL = "http://elib.shpl.ru/pages/{}/zooms/6"

    @staticmethod
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

    @override
    def fetch_book_data(book_url: str, event_dispatcher: BookEventSystem) -> dict:
        library_id = OnlineLibrary.PRLIB.value
        library_book_id = book_url.split("/")[-1]

        # Read html doc
        html_doc = DownloadStrategy.get_html_doc(book_url)
        if html_doc is None:
            return None

        # Parse it
        title = SphlStrategy.parse_html_for_key(html_doc, key="Заглавие")
        if title is None:
            title = library_book_id
        author = SphlStrategy.parse_html_for_key(html_doc, key="Автор")
        year = SphlStrategy.parse_html_for_key(html_doc, "Год издания")
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

    @override
    def download_images(
        book: IBook,
        root_folder: str,
        event_dispatcher: BookEventSystem,
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
                im_address = SphlStrategy.SCAN_URL.format(im)
                try:
                    # im_cmd = f'curl {im_address} -o "{str(image_path)}"'
                    # system_call(im_cmd)
                    DownloadStrategy.download_image(im_address, image_path)
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
        DownloadStrategy.create_pdf(book_dest_folder, book, event_dispatcher)

        return book

    @override
    def can_handle_url(book_url: str) -> bool:
        return "elib.shpl.ru" in book_url
