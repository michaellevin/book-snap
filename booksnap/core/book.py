from __future__ import (
    annotations,
)  # PEP 563. This is needed for the type hinting of the classmethod 'create_instance'


from dataclasses import dataclass, field, fields, asdict, InitVar
from typing import Optional, Dict, Any, Type
from types import SimpleNamespace
from pprint import pprint

from .enums import OnlineLibrary, BookState
from .utils import hash_url


@dataclass
class IBook:
    """Interface for a book.

    For details on dataclasses, see https://docs.python.org/3/library/dataclasses.html.
    For visual demonstration, see book.drawio.

    Attributes
    ----------
    url : str
        The URL of the book in the library.
    library_book_id : str
        The unique identifier of the book in the online library - the stem of url path
        e.g., for url = 'http://example.com/book1/12345', library_book_id = '12345'.
    library : OnlineLibrary
        The online library enumeration (see enums.py).
    title : str
        The title of the book.
    author : str
        The author of the book.
    num_pages : int
        The total number of pages in the book.
    year : Optional[int]
        The year of publication of the book (default is None because usually it is hard to retrieve).
    state : Optional[BookState]
        The current download state of the book , e.g., PDF_READY (see enums.py).
        Usage:
            self.set_state(state: BookState) sets the state of the book.
    _progress_page : Optional[int]
        The last downloaded page.
        Usage:
            self.set_progress_page(page: int) sets the last downloaded page.
            self.progress_page returns the last downloaded page.
    _tech_dict : InitVar(Dict)
        This is a dictionary that will be used to store technical data.
        When the book instance is created, the '_tech_dict' is passed as an InitVar.
        Then, after __post_init__, the '_tech_dict' is converted to a SimpleNamespace object,
        stored as '_tech'.
    _tech: SimpleNamespace
        This is a SimpleNamespace object that will be used to store technical data.
        It is created from '_tech_dict' in __post_init__.
        Usage:
            self._tech.ids
            self._tech.all_images
            self._tech.some_other_data

            self.get_tech() returns the SimpleNamespace object.
    Methods
    -------
    __post_init__(_tech_dict: Optional[Dict]) -> None:
        Operations to perform after the initial creation of the dataclass instance.
            A. generate 'id' as a hash of the book's URL.
            B. genetate '_tech' attribute from '_tech_dict' if it is not None.
                The reason is to get a SimpleNamespace object that can be easily accessed as
                    self._tech.ids
                and not as
                    self._tech_dict['ids'].
                Because the latter is not convenient to use. The '_tech_dict' is then abandoned,
                its lifespan ends after __post_init__ because it is InitVar by design.
    @classmethod
    create_instance(book_data: Dict[str, Any]) -> IBook:
        Create a new IBook instance from a dictionary of book data, ensuring only valid fields are used.
    id() -> int:
        Returns the unique identifier of the book in our library (hash from the path).
    progress_page() -> int:
        Returns the last downloaded page index.
    set_progress_page(page: int):
        Sets the last downloaded page index.
    set_state(state: BookState):
        Update the download state of the book.
    get_tech() -> SimpleNamespace:
        Retrieves the technical details related to the book, stored as a SimpleNamespace.
    to_dict(final: bool = False) -> dict:
        Returns the book's information as a dictionary, optionally excluding private attributes.
    pprint():
        Pretty-prints the book's information.

    Examples
    --------
    Creating an instance of IBook:

        >>> book_data = {
        ...     'url': 'http://example.com/book1/12345',
        ...     'library_book_id': '12345',
        ...     'library': OnlineLibrary.LIBRARY_A,
        ...     'title': 'Example Book',
        ...     'author': 'John Doe',
        ...     'num_pages': 250,
        ...     'year': 2021,
                '_tech_dict': {
                                ids': [..., ..., ],
                                'all_images': [..., ...,],
                            }
        ... }
        >>> book = IBook.create_instance(book_data)
        >>> print(book)
        IBook(url='http://example.com/book1', library_book_id='12345', library=OnlineLibrary.LIBRARY_A, title='Example Book', author='John Doe', num_pages=250, year=2021, state=None, _progress_page=None)
    or:
        >>> book = IBook(**{'url': 'http://example.com/book1/12345',
        ...     'library_book_id': '12345',
        ...     'library': OnlineLibrary.LIBRARY_A,
        ...     'title': 'Example Book',
        ...     'author': 'John Doe',
        ...     'num_pages': 250,
        ...     'year': 2021
        ...     })


    Setting and getting the progress:

        >>> book.set_progress_page(25)
        >>> print(book.progress_page) # 25

    Updating and retrieving the book state:

        >>> book.set_state(BookState.PDF_READY)
        >>> print(book.state) # BookState.PDF_READY

    Converting the book data to a dictionary:

        >>> book_dict = book.to_dict(final=True)
        >>> print(book_dict)
        {'url': 'http://example.com/book1/12345', 'library_book_id': '12345', 'library': <OnlineLibrary.LIBRARY_A: 1>, 'title': 'Example Book', 'author': 'John Doe', 'num_pages': 250, 'year': 2021, 'state': <BookState.AVAILABLE: 1>}

    Pretty-printing the book data:

        >>> book.pprint()
        Title: Example Book
        Author: John Doe
        Number of pages: 250
        URL: http://example.com/book1/12345
        ID: 123456789  # this is a mock value, actual value will depend on the hash function
        Library book ID: 12345
        Library: LIBRARY_A
        State: PDF_READY
        Progress page: 25
    """

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

    def __post_init__(self, _tech_dict: Optional[Dict]) -> None:
        """Operations to perform after the initial creation of the dataclass instance."""
        self._id = hash_url(self.url)
        if _tech_dict is not None:
            for key, value in _tech_dict.items():
                setattr(self._tech, key, value)

    @classmethod
    def create_instance(cls: Type[IBook], book_data: Dict[str, Any]) -> IBook:
        """
        Create a new IBook instance from a dictionary of book data, ensuring only valid fields are used.

        :param book_data: Dictionary containing book data.
        :return: An instance of IBook.
        """
        valid_fields = {field.name for field in fields(cls) if field.init}
        # Only keep items in book_data whose keys correspond to valid_fields.
        filtered_data = {k: v for k, v in book_data.items() if k in valid_fields}
        # '_tech_dict' needs special handling since it's an InitVar. If present, it should be passed separately.
        _tech_dict_data = book_data.get("_tech_dict")
        if _tech_dict_data is not None:
            return cls(
                **filtered_data, _tech_dict=_tech_dict_data
            )  # Create an instance with _tech_dict.

        return cls(**filtered_data)  # Regular instance creation.

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
        # Check if it is not empty namespace
        is_namespace_empty = not bool(self._tech.__dict__)
        if is_namespace_empty:
            return None
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
            book_dict["_tech_dict"] = vars(self._tech)
            book_dict.pop("_tech")

        # Remove items where value is None
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
    #         repr_str +=
    def pprint(self) -> None:
        """Pretty-print the book data."""
        print(f"Title: {self.title}")
        print(f"Author: {self.author}")
        print(f"Number of pages: {self.num_pages}")
        print(f"URL: {self.url}")
        print(f"ID: {self.id}")
        print(f"Library book ID: {self.library_book_id}")
        print(f"Library: {str(OnlineLibrary(self.library))}")
        print(f"State: {str(BookState(self.state))}")
        print(f"Progress page: {self.progress_page}")
        if tech := self.get_tech():
            print(f"Technical data:")
            pprint(vars(tech))
