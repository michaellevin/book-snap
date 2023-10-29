import sys
import os
import pprint
from logging import getLogger

logger = getLogger(__name__)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QProgressBar,
)
from PySide6.QtCore import Qt, Slot, QMetaObject, Q_ARG

from ..core import LibraryMinistry, BookState, IBook


class SimpleApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.urls = [
            "https://www.prlib.ru/item/331483",
        ]
        self.book = None
        self.library_ministry = LibraryMinistry()
        self.library = self.library_ministry.build_library(".LIBRARY")
        # self.library._clear_metadata()  # temporary

        self.library.on_book_data_fetched.connect(self.register_book_event)
        self.library.on_book_progress.connect(self.update_book_progress_event)
        self.library.on_book_images_downloaded.connect(self.images_downloaded_event)
        self.library.on_book_data_ready.connect(self.book_is_ready_event)

        # Set main window properties
        self.setWindowTitle("Simple Downloader")
        self.setGeometry(300, 300, 600, 400)  # Set the position and size of the window

        # Create a layout
        layout = QVBoxLayout()

        # Create a "Query " button
        self.query_btn = QPushButton("Query")
        self.query_btn.clicked.connect(self.query)
        layout.addWidget(self.query_btn)

        # Create a "Start Download" button
        self.download_btn = QPushButton("Start Download")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        # Create a "Shutdown" button
        self.shutdown_btn = QPushButton("Shutdown")
        self.shutdown_btn.clicked.connect(self.shutdown)
        layout.addWidget(self.shutdown_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.progress_bar.setRange(0, 100)
        stylesheet = """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center; /* align the text in the center */
                height: 6px; /* same as the chunk widths */
                background-color: #4CAF50;  /* A nice shade of green */
            
                /* Text styling */
                color: #FFFFFF;  /* White text for good readability */
                font: bold 11px;  /* Bold, 11-point font (or whichever size suits your UI) */
                text-align: center;  /* Center-aligned text */
            }

            QProgressBar::chunk {
                background-color: #8BC34A; 
                width: 10px; /* make "chunk" rectangles 10px wide */
                margin: 1px; /* space between the chunks */
            }
        """
        self.progress_bar.setStyleSheet(stylesheet)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.open_btn = QPushButton("---")
        layout.addWidget(self.open_btn)
        self.open_btn.clicked.connect(self.open_book)

        # Set the layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def query(self):
        # Logic to query the library
        logger.info(f"Querying a book: {self.urls[0]}")
        self.book = self.library.query_book(book_url=self.urls[0])
        if self.book:
            self.book.pprint()
        else:
            logger.warning("Book not found.")

    @Slot()
    def start_download(self):
        # Logic to start the download
        book_future = self.library.get_book(self.urls[0])
        return book_future

    @Slot()
    def shutdown(self):
        # Logic to handle shutdown
        logger.warning(" ================= Shutting down =================")
        self.library._download_manager.abort(self.urls[0])

    def update_textbox(self, book: IBook):
        f_book_data = pprint.pformat(book.to_dict())
        # Ensure that UI updates happen in the Qt main thread
        QMetaObject.invokeMethod(
            self.text_edit,
            "setText",
            Qt.QueuedConnection,
            Q_ARG(str, f_book_data),
        )

    def register_book_event(self, book: IBook):
        self.open_btn.setText(f"Book {book.title} is fetched")
        self.update_textbox(book)

    def update_book_progress_event(self, book: IBook):
        self.progress_bar.setValue(100 * book.progress_page / book.num_pages)
        self.update_textbox(book)

    def images_downloaded_event(self, book: IBook):
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("PDF is ready")
        self.update_textbox(book)

    def book_is_ready_event(self, book: IBook):
        # Ensure that UI updates happen in the Qt main thread
        self.open_btn.setText(f"Open {book.title}")
        self.book = book
        self.update_textbox(book)

    def open_book(self):
        # Logic to open the book
        if self.book is None:
            logger.info("Book not found")
        else:
            if self.book.state == BookState.PDF_READY.value:
                logger.info(self.library.get_book_path(self.book))
            else:
                logger.info("Book not ready")

    def closeEvent(self, event) -> None:
        self.library.stop()
        return super().closeEvent(event)


def main():
    app = QApplication([])

    window = SimpleApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
