from dataclasses import dataclass, field
import hashlib


@dataclass
class IBook:
    library_url: str
    library_id: int
    title: str
    author: str
    num_pages: int
    year: int = None  # This sets a default value for 'year'

    # The '_id' is not specified upon creation; it will be generated in the '__post_init__'
    _id: int = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        """Operations to perform after the initial creation of the dataclass instance."""
        self._id = self._generate_id_from_url(self.library_url)

    @staticmethod
    def _generate_id_from_url(url: str) -> int:
        """
        Generate a unique integer ID from the library URL.
        This example uses a hash function to ensure the uniqueness of the ID,
        converting the hash to an integer to be used as the ID.
        """
        # Create a hash of the URL
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        # Convert the hash to an integer. We use only the first few characters to avoid large numbers.
        unique_id = int(
            url_hash[:10], 16
        )  # This will convert the hexadecimal hash substring to an integer.
        return unique_id

    @property
    def id(self) -> int:
        """Get the unique ID of the book."""
        return self._id

    # def __repr__(self) -> str:
    #     # Construct the base part of the string
    #     repr_str = f"{self.title} by {self.author}"

    #     # Add the year if it is not None
    #     if self.year is not None:
    #         repr_str += f" ({self.year})"

    #     return repr_str
