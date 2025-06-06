from abc import ABC, abstractmethod
from typing import List, Dict

class ISiteScraper(ABC):
    @abstractmethod
    def scrape_site(self) -> List[Dict]:
        pass

    @abstractmethod
    def _extract_listing_details(self, html_element) -> Dict:
        pass

    @abstractmethod
    def _extract_post_details(self, post_url: str) -> Dict:
        pass
