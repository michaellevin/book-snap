from dataclasses import dataclass, field, asdict, InitVar
from typing import Optional, Dict, Any
from types import SimpleNamespace

from .enums import OnlineLibrary, BookState
from .utils import hash_url


@dataclass
class IBook:
    url: str
    library_book_id: str
    library: OnlineLibrary
    title: str
    author: str
    num_pages: int
    year: Optional[int] = None  # This sets a default value for 'year'
    state: Optional[BookState] = None
    _progress_page: Optional[int] = None

    # This will not be attribute due to InitVar
    _tech_dict: InitVar[Optional[Dict]] = None
    # This will be an attribute: a dictionary that will be used to store technical data
    _tech: SimpleNamespace = field(init=False, default_factory=SimpleNamespace)
    # The '_id' is not specified upon creation; it will be generated in the '__post_init__'
    _id: int = field(init=False, repr=False, compare=False)

    def __post_init__(self, _tech_dict: Optional[Dict]):
        """Operations to perform after the initial creation of the dataclass instance."""
        self._id = hash_url(self.url)

        if _tech_dict is not None:
            for key, value in _tech_dict.items():
                setattr(self._tech, key, value)

    @property
    def id(self) -> int:
        """Get the unique ID of the book."""
        return self._id

    @property
    def progress_page(self) -> int:
        """Get the progress page of the book."""
        return self._progress_page

    def set_progress_page(self, page: int) -> None:
        """Set the progress page of the book."""
        self._progress_page = page

    def set_state(self, state: BookState) -> None:
        """Set the state of the book."""
        self.state = state

    def get_tech(self) -> SimpleNamespace:
        """Get the technical data of the book."""
        return self._tech

    def to_dict(self, final: bool = False) -> dict:
        """
        Convert the dataclass to a dictionary format that can be serialized to JSON.
        This includes converting the SimpleNamespace into a dictionary.
        Excludes attributes with value None.

        args:
            final (bool): If True, exclude attributes starting with '_'.
        """

        book_dict = asdict(self)

        # Convert the SimpleNamespace to a dictionary
        if isinstance(self._tech, SimpleNamespace):
            book_dict["_tech"] = vars(self._tech)

        # Remove items where value is None
        # (TODO): check progress_page
        return {
            k: v
            for k, v in book_dict.items()
            if v is not None and (not final or not k.startswith("_"))
        }

    # def __repr__(self) -> str:
    #     # Construct the base part of the string
    #     repr_str = f"{self.title} by {self.author}"

    #     # Add the year if it is not None
    #     if self.year is not None:
    #         repr_str += f" ({self.year})"

    #     return repr_str

    def pprint(self) -> None:
        """Pretty-print the book data."""
        print(f"Title: {self.title}")
        print(f"Author: {self.author}")
        print(f"Year: {self.year if self.year is not None else 'Unknown'}")
        print(f"Number of pages: {self.num_pages}")
        print(f"State: {BookState(self.state)}")
        print(f"Progress page: {self.progress_page}")
        print(f"URL: {self.url}")
        print(f"Library book ID: {self.library_book_id}")
        print(f"Library: {OnlineLibrary(self.library)}")
