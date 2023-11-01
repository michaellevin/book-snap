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


class ShplStrategy(DownloadStrategy):
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
        title = ShplStrategy.parse_html_for_key(html_doc, key="Заглавие")
        if title is None:
            title = library_book_id
        author = ShplStrategy.parse_html_for_key(html_doc, key="Автор")
        year = ShplStrategy.parse_html_for_key(html_doc, "Год издания")
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
        book,
        root_folder,
        event_dispatcher,
        start_page=0,
        timeout=90,
        main_event=None,
    ):
        return DownloadStrategy.download_images(
            book,
            root_folder,
            event_dispatcher,
            start_page,
            timeout,
            main_event,
            get_ids_func=lambda book: book.get_tech().image_ids,
            construct_address_func=lambda i, ids: ShplStrategy.SCAN_URL.format(ids[i]),
            download_func=DownloadStrategy.download_image,
        )

    @override
    def can_handle_url(book_url: str) -> bool:
        return "elib.shpl.ru" in book_url
