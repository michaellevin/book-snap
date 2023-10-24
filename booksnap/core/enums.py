from enum import Enum, auto


class OnlineLibrary(Enum):
    PRLIB = auto()  # Each call to auto() generates a unique value
    SHPL = auto()
    # Add other libraries here


class BookState(Enum):
    REGISTERED = auto()
    DOWNLOADING = auto()
    TERMINATED = auto()
    DOWNLOAD_FINISHED = auto()
    PDF_READY = auto()
