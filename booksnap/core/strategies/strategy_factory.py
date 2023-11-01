from ._strategy import DownloadStrategy
from .prlib import PrLibStrategy
from .shpl import ShplStrategy


class DownloadStrategyFactory:
    @staticmethod
    def get_strategy(book_url: str) -> DownloadStrategy:
        """Get the appropriate download strategy for the given URL."""
        # List all possible strategies here
        strategies = [
            PrLibStrategy,
            ShplStrategy,
        ]  # Add more as you implement them

        # Select the appropriate strategy based on the URL
        if any((strategy := s).can_handle_url(book_url) for s in strategies):
            return strategy

        raise ValueError(f"No available strategy for the URL: {book_url}")
