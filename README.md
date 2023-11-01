[![CodeFactor](https://www.codefactor.io/repository/github/michaellevin/book-snap/badge)](https://www.codefactor.io/repository/github/michaellevin/book-snap)

# BookSnap

![BookSnap](docs/screenshots/shpl_screen1.png)

While many online libraries offer users the ability to view books online, few allow downloading the entire book as a PDF. The traditional method of accessing these books online requires users to click on each page and wait for every image to load. This process is not only time-consuming but also inconvenient for those who want to quickly navigate through the entirety of a book.

**BookSnap** aims to simplify this process. This project is designed to automatically download all the images from a book's online page and assemble them into a single, easily navigable PDF file, which will then be stored in a designated local library folder on your computer.

## Supported Libraries

Currently, BookSnap supports the following Russian libraries:

- [President's Library](https://www.prlib.ru/)
- [State Historic Public Library](http://elib.shpl.ru/)

We are open to extending support to more libraries. However, each library requires its unique strategy to fetch book images.

## Prerequisites:

- Python 3.12
- Libraries: 
  - requests
  - beautifulsoup4
  - img2pdf

## Installation:

1. Clone the repository:
```bash
git clone https://github.com/michaellevin/book-snap.git
```
2. Navigate to the project directory and install the required packages:
```bash
pip install -r requirements.txt
```
## Usage:
```python
import booksnap

# Initialize a library creator object (you may want to have several separate library folders)
library_ministry = booksnap.LibraryMinistry()

# Create a `library` object and specify where you'd like to store your books
library = library_ministry.build_library("path/to/store/books")

# Get a book (returs path to the book or Future object if the book is not yet downloaded)
future_book = library.get_book("https://www.prlib.ru/item/331483")
```

The last command initiates the book download if it's not present in the designated library. If the book is already available, it will simply return its path. Should the download be interrupted for any reason, the program will automatically resume from the last downloaded page.

The future_book can either be a `concurrent.futures.Future` object or a pathlib.Path object.

A sample usage of the library can be found in the `run.py` file.


## GUI Application (In Development)
For those interested in a graphical interface, there are several signals (similar to Qt signals) that can be connected to:

```python
library.on_book_data_fetched.connect(your_function)
library.on_book_progress.connect(your_function)
library.on_book_images_downloaded.connect(your_function)
library.on_book_data_ready.connect(your_function)
```
These signals correspond to various events, such as:

- Initial data fetch from the provided URL
- Download progress (current page)
- Completion of image downloads
- Availability of the final PDF

A sample usage of these signals can be found in the `run_ui.py` file, which references `booksnap/ui/simple_viewer.py`. For this GUI, you will need to install `PySide6`.

### Note
When downloading from the **President's Library**, there's no need for any delay between requests. However, the **State Historic Public Library** requires a 90-second timeout between requests. This naturally prolongs the download process but ensures successful downloads in the end.

## Contributing:
Downloading images from the **President's Library** is facilitated by the tool [**dezoomify-rs**](https://github.com/lovasoa/dezoomify-rs). This versatile tool is designed to download zoomable images from platforms such as Google Arts & Culture, Zoomify, IIIF, and more. Many thanks to the authors for developing this invaluable tool.


## TODO
- Develop a comprehensive interface using Flutter.

## Under the Hood
UML diagrams can be found in the `docs` folder.

![Library Description](docs/uml/Library.drawio)


