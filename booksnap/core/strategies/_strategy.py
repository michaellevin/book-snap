from abc import ABC, abstractmethod

from pathlib import Path
from typing import Optional
import requests
import img2pdf
import glob
import logging

logger = logging.getLogger(__name__)

from ..events import EventSystem
from ..book import IBook
from ..enums import BookState, EventType


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

    @staticmethod
    def get_html_doc(book_url):
        html_doc = None
        try:
            response = requests.get(book_url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.critical(f"HTTP error occurred: {err}")
        html_doc = response.text
        logger.info(f"Book data fetched from {book_url}")
        return html_doc

    @staticmethod
    def download_image(url, path):
        """Downloads an image from a given URL and saves it to the specified path.

        Args:
            url (str): The URL of the image.
            path (str): The local path to save the downloaded image.

        Raises:
            RuntimeError: If the download fails.
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Save the image.
            with open(path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

        except requests.RequestException as e:
            raise RuntimeError(f"Image download failed: {str(e)}") from e

    @staticmethod
    def _create_pdf(dest_folder: str, title: str) -> str:
        """Converts all jpeg images in the specified folder to a single PDF and deletes the images.

        :param dest_folder: Folder containing jpeg images.
        :param title: Title of the resulting PDF file.
        """
        # Convert paths to Path objects, which are more versatile
        dest_folder_path = Path(dest_folder)
        pdf_path = dest_folder_path.parent / f"{title}.pdf"

        # Find all JPEG images in the destination folder
        imgs = glob.glob(str(dest_folder_path / "*.jpeg"))

        # Create a PDF from the images
        try:
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(imgs))
        except Exception as e:
            print(f"An error occurred while creating the PDF: {e}")
            return None

    def create_pdf(book_dest_folder, book, event_dispatcher):
        try:
            DownloadStrategy._create_pdf(book_dest_folder, book.title)
            event_dispatcher.emit(
                EventType.BOOK_IS_READY, book, state=BookState.PDF_READY
            )
        except RuntimeError as err:
            logger.critical(err)
            event_dispatcher.emit(
                EventType.IMAGES_DOWNLOADED, book, state=BookState.TERMINATED
            )
