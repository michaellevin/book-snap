class IBook(object):
    def __init__(self, title, author, year=None):
        self._title = title
        self._author = author
        self._year = year
        self._numpages = 0

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def year(self) -> int:
        return self._year

    @property
    def numpages(self) -> int:
        return self._numpages

    @numpages.setter
    def numpages(self, value):
        self._numpages = value

    def __repr__(self):
        return "{} by {} ({})".format(self.title, self.author, self.year)
