import sys
from PySide6.QtWidgets import QApplication
import booksnap

url_book_6pages = "https://www.prlib.ru/item/331483"
url_book_24pages = "http://elib.shpl.ru/ru/nodes/13552"
url_book_1page = "http://elib.shpl.ru/ru/nodes/12430"


app = QApplication([])
window = booksnap.SimpleApp()
window.show()
sys.exit(app.exec())
