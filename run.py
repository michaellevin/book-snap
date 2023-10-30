from pprint import pprint
import booksnap

library_ministry = booksnap.LibraryMinistry()
library = library_ministry.build_library(".LIBRARY")
url_book_6pages = "https://www.prlib.ru/item/331483"
url_book_24pages = "http://elib.shpl.ru/ru/nodes/13552"
url_book_1page = "http://elib.shpl.ru/ru/nodes/12430"
future_book = library.get_book(url_book_24pages)
future_book.result()

# import sys
# from PySide6.QtWidgets import QApplication
# app = QApplication([])
# window = booksnap.SimpleApp()
# window.show()
# sys.exit(app.exec())
