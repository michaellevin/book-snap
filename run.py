import os
import sys
from pprint import pprint
import booksnap

library_ministry = booksnap.LibraryMinistry()
library = library_ministry.build_library(".LIBRARY")
url_book_6pages = "https://www.prlib.ru/item/331483"
# library.download_book(url_book_6pages, resume=False)
library.get_book(url_book_6pages)  # .pprint()
