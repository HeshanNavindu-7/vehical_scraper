# src/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict

class ISiteScraper(ABC):
    """
    Abstract Base Class (Interface) for web scraping sites.
    Defines the contract for any site-specific scraper.
    (Strategy Pattern)
    """

    @abstractmethod
    def scrape_site(self) -> List[Dict]:
        """
        Main method to initiate scraping for a specific website.
        Should return a list of dictionaries, where each dictionary
        represents a scraped vehicle listing.
        """
        pass

    @abstractmethod
    def _extract_listing_details(self, html_element) -> Dict:
        """
        Abstract method to extract details from a single listing HTML element.
        """
        pass

    @abstractmethod
    def _extract_post_details(self, post_url: str) -> Dict:
        """
        Abstract method to visit a post's detail page and extract more specific info.
        """
        pass