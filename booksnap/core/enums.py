from enum import Enum, auto


class OnlineLibrary(Enum):
    PRLIB = auto()  # Each call to auto() generates a unique value
    SHPL = auto()
    # Add other libraries here


class Status(Enum):
    DOWNLOADING = auto()
    DOWNLOADED = auto()
    FAILED = auto()
