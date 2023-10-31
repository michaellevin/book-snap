from pprint import pprint
import booksnap

library_ministry = booksnap.LibraryMinistry()
library = library_ministry.build_library(".LIBRARY")
prlib_test_6p = "https://www.prlib.ru/item/331483"
sphl_test_24p = "http://elib.shpl.ru/ru/nodes/13552"
sphl_test_1p = "http://elib.shpl.ru/ru/nodes/12430"
future_book = library.get_book(sphl_test_24p)
future_book.result()

# import sys
# from PySide6.QtWidgets import QApplication
# app = QApplication([])
# window = booksnap.SimpleApp()
# window.show()
# sys.exit(app.exec())
