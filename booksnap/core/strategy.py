from abc import ABC, abstractmethod


class DownloadStrategy(ABC):
    @abstractmethod
    def download(self, book_url: str) -> None:
        """Download the book from the given URL."""
        pass

    @staticmethod
    @abstractmethod
    def can_handle_url(book_url: str) -> bool:
        """Check if the strategy can handle the given URL."""
        pass


class PrLibDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for PrLib.
    """

    def download(self, book_url: str) -> None:
        # Logic for downloading a book from PrLib
        pass

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "prlib.ru" in book_url


class SPHLDownloadStrategy(DownloadStrategy):
    """
    This class implements the DownloadStrategy interface for SPHL.
    """

    def download(self, book_url: str) -> None:
        # Logic for downloading a book from ELib
        pass

    @staticmethod
    def can_handle_url(book_url: str) -> bool:
        return "elib.shpl.ru" in book_url


class DownloadStrategyFactory:
    @staticmethod
    def get_strategy(book_url: str) -> DownloadStrategy:
        """Get the appropriate download strategy for the given URL."""
        # List all possible strategies here
        strategies = [
            PrLibDownloadStrategy,
            SPHLDownloadStrategy,
        ]  # Add more as you implement them

        # Select the appropriate strategy based on the URL
        for strategy in strategies:
            if strategy.can_handle_url(book_url):
                return strategy()

        raise ValueError(f"No available strategy for the URL: {book_url}")
