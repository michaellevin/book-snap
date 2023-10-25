from ._singleton import SingletonMeta
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

from .library import Library


class LibraryMinistry(metaclass=SingletonMeta):
    def __init__(self):
        self._libraries = {}

    def build_library(self, books_dir: str) -> Library:
        if self._libraries.get(books_dir) is None:
            self._libraries[books_dir] = Library(books_dir)
            logger.info(
                f"New Library is built! Please visit us: {books_dir}, 24/7 open"
            )
        return self._libraries[books_dir]

    def get_library(self, books_dir: str) -> Library:
        library = self._libraries.get(books_dir)
        if library is None:
            raise ValueError(
                f"No library exists at {books_dir}"
            )  # or handle this some other appropriate way
        return library

    def get_all_libraries(self) -> dict:
        return self._libraries
