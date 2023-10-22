from dataclasses import dataclass, field, asdict
from .enums import OnlineLibrary, Status
from typing import Optional
from .utils import generate_id_from_url


@dataclass
class IBook:
    url: str
    library_book_id: str
    library: OnlineLibrary
    title: str
    author: str
    num_pages: int
    year: Optional[int] = None  # This sets a default value for 'year'

    status: Optional[Status] = None
    progress_page: Optional[int] = None

    # The '_id' is not specified upon creation; it will be generated in the '__post_init__'
    _id: int = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        """Operations to perform after the initial creation of the dataclass instance."""
        self._id = generate_id_from_url(self.url)

    @property
    def id(self) -> int:
        """Get the unique ID of the book."""
        return self._id

    def to_dict(self) -> dict:
        """
        Convert the dataclass to a dictionary, excluding attributes with value None.
        """
        book_dict = asdict(self)  # Convert the dataclass to a dictionary
        # Remove items where value is None
        filtered_book_dict = {
            k: v
            for k, v in book_dict.items()
            if v is not None and not k.startswith("_")
        }
        return filtered_book_dict

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
        print(f"Status: {Status(self.status)}")
        print(f"Progress page: {self.progress_page}")
        print(f"URL: {self.url}")
        print(f"Library book ID: {self.library_book_id}")
        print(f"Library: {OnlineLibrary(self.library)}")
