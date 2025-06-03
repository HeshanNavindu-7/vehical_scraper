# src/riyasewana_scraper.py
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from typing import List, Dict

from .interfaces import ISiteScraper # Importing the interface for Strategy Pattern
from .db_manager import DatabaseManager # For interacting with the database
from .utils import setup_logging, safe_urljoin, tqdm # Helper utilities
from .config import (
    RIYASWANA_BASE_URL, RIYASWANA_VEHICLE_TYPES, RIYASWANA_VEHICLE_MAKES,
    DELAY_RANGE_PAGE_LOAD_SEC, DELAY_RANGE_POST_LOAD_SEC, RIYASWANA_SELECTORS,
    DB_BATCH_INSERT_SIZE
)

logger = setup_logging()

class RiyasewanaScraper(ISiteScraper):
    """
    Concrete implementation of the ISiteScraper interface for Riyasewana.com.
    This class contains all the specific logic for scraping Riyasewana.
    (Strategy Pattern Implementation)
    """
    def __init__(self, driver: webdriver.Chrome, db_manager: DatabaseManager):
        """
        Initializes the RiyasewanaScraper.
        
        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance (Dependency Injection).
            db_manager (DatabaseManager): The database manager instance (Dependency Injection).
        """
        self.driver = driver
        self.db_manager = db_manager
        
        # Configuration loaded from config.py
        self.base_url = RIYASWANA_BASE_URL
        self.vehicle_types = RIYASWANA_VEHICLE_TYPES
        self.vehicle_makes = RIYASWANA_VEHICLE_MAKES
        self.delay_page = DELAY_RANGE_PAGE_LOAD_SEC
        self.delay_post = DELAY_RANGE_POST_LOAD_SEC
        self.selectors = RIYASWANA_SELECTORS
        self.batch_size = DB_BATCH_INSERT_SIZE
        
        # Load already seen URLs from the database to avoid re-scraping
        self.seen_urls = db_manager.get_all_post_urls()
        logger.info(f"RiyasewanaScraper initialized. Loaded {len(self.seen_urls)} existing URLs from DB.")

    def scrape_site(self) -> List[Dict]:
        """
        Orchestrates the entire scraping process for Riyasewana.com.
        Iterates through configured vehicle types and makes, handles pagination,
        and scrapes both listing overview pages and individual detail pages.
        """
        all_new_listings_scraped = []
        current_batch_for_db = [] # Buffer for batch database inserts

        # Outer progress bar for types x makes combinations
        with tqdm(total=len(self.vehicle_types) * len(self.vehicle_makes), desc="Scraping Riyasewana (Types x Makes)") as pbar_outer:
            for make in self.vehicle_makes:
                for vehicle_type in self.vehicle_types:
                    logger.info(f"Starting scrape for Type: '{vehicle_type}', Make: '{make}'")
                    page = 1
                    
                    while True: # Loop through pagination
                        url = f"{self.base_url}/search/{vehicle_type}/{make}"
                        if page > 1:
                            url = f"{url}?page={page}"
                        
                        logger.info(f"Visiting listing page {page}: {url}")
                        try:
                            self.driver.get(url)
                            time.sleep(random.uniform(*self.delay_page)) # Polite delay
                            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        except Exception as e:
                            logger.error(f"Failed to load listing page {url}: {e}", exc_info=True)
                            break # Break pagination for current make/type if page load fails

                        content_div = soup.find('div', id='content') # Assuming 'content' ID for main content
                        ul_tag = content_div.find('ul') if content_div else None
                        
                        if not ul_tag:
                            logger.info(f"No 'ul' tag found or end of pages for {vehicle_type}/{make} on page {page}.")
                            break # No listings container found, likely end of results

                        li_tags = ul_tag.find_all(self.selectors['LISTING_CONTAINER'])
                        if not li_tags:
                            logger.info(f"No listing items found (li_tags) for {vehicle_type}/{make} on page {page}.")
                            break # No more individual listings on this page

                        new_listings_on_page = 0
                        for li in li_tags:
                            listing_overview_data = self._extract_listing_details(li)
                            post_url = listing_overview_data.get('post_url')

                            # Skip if no URL or if already processed in this session or previous runs
                            if not post_url or post_url in self.seen_urls:
                                logger.debug(f"Skipping already seen or invalid URL: {post_url}")
                                continue 

                            self.seen_urls.add(post_url) # Mark as seen for current session to avoid duplicates within same run

                            logger.debug(f"➡️ Visiting post: {post_url}")
                            try:
                                details_from_post = self._extract_post_details(post_url)
                                # Merge overview and detailed data
                                full_listing_data = {
                                    **listing_overview_data, 
                                    **details_from_post,
                                    'make': make, # Add make and type from the search context
                                    'type': vehicle_type
                                } 
                                
                                all_new_listings_scraped.append(full_listing_data)
                                current_batch_for_db.append(full_listing_data)
                                new_listings_on_page += 1

                                # Perform batch insert if batch size is reached
                                if len(current_batch_for_db) >= self.batch_size:
                                    self.db_manager.insert_listings_batch(current_batch_for_db)
                                    current_batch_for_db = [] # Reset batch after insertion
                            except Exception as e:
                                logger.error(f"Error processing detail page {post_url}: {e}", exc_info=True)
                                # Continue to next listing even if detail page fails, don't stop the whole scrape

                        # If no new unique listings were found on a subsequent page, assume end of results
                        if new_listings_on_page == 0 and page > 1: 
                            logger.info(f"No new unique listings found on page {page}. Ending pagination for {vehicle_type}/{make}.")
                            break 

                        page += 1
                    pbar_outer.update(1) # Update outer progress bar per make/type combination
        
        # Insert any remaining listings in the batch after all loops finish
        if current_batch_for_db:
            self.db_manager.insert_listings_batch(current_batch_for_db)
        
        logger.info(f"Riyasewana scraping completed. Total new unique listings processed: {len(all_new_listings_scraped)}")
        return all_new_listings_scraped

    def _extract_listing_details(self, li_tag) -> Dict:
        """
        Extracts high-level details from a single listing item (li_tag) on the search results page.
        Handles potential missing elements gracefully by returning empty strings.
        """
        data = {}
        try:
            h2_tag = li_tag.find('h2')
            a_tag = h2_tag.find('a') if h2_tag else None
            
            data['title'] = a_tag.text.strip() if a_tag else ""
            
            # Use safe_urljoin for robust URL construction
            post_url_relative = a_tag['href'] if a_tag and 'href' in a_tag.attrs else ""
            data['post_url'] = safe_urljoin(self.base_url, post_url_relative)

            img_tag = li_tag.find('img')
            image_url_relative = img_tag['src'].strip() if img_tag and 'src' in img_tag.attrs else ""
            # Riyasewana often uses protocol-relative URLs (e.g., //img.riyasewana.com/...)
            data['image_url'] = safe_urljoin("https:", image_url_relative) 

            date_div = li_tag.find('div', class_=self.selectors['LISTING_DATE'])
            data['date'] = date_div.text.strip() if date_div else ""

            # Extract mileage, price, location from common text boxes
            data['location'] = ""
            data['overview_price'] = ""
            data['mileage'] = ""
            boxintxts = li_tag.find_all('div', class_=self.selectors['LISTING_BOX_TEXTS'])
            for box in boxintxts:
                txt = box.text.strip()
                if "km" in txt.lower():
                    data['mileage'] = txt
                elif "rs" in txt.lower() or "negotiable" in txt.lower():
                    data['overview_price'] = txt
                # Assuming the remaining unique text is the location
                elif txt and txt not in [data['overview_price'], data['mileage'], data['date']]:
                    data['location'] = txt 

        except AttributeError as e:
            logger.warning(f"Missing expected HTML element in listing overview: {e}. Partial HTML: {li_tag.prettify()[:200]}...")
        except Exception as e:
            logger.error(f"Unexpected error extracting listing overview: {e}", exc_info=True)
        return data

    def _extract_post_details(self, post_url: str) -> Dict:
        """
        Visits a single vehicle post page and extracts detailed specifications from its table.
        Optimized by building a lookup map from all table cells once.
        """
        details = {}
        try:
            self.driver.get(post_url)
            time.sleep(random.uniform(*self.delay_post)) # Polite delay for post page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract all relevant table cells once
            all_cells = soup.select(self.selectors['POST_DETAIL_TABLE_CELLS'])
            
            # Build a dictionary for quick lookups (assuming label-value pairs in table)
            details_map = {}
            for i in range(0, len(all_cells), 2):
                label_cell = all_cells[i]
                if i + 1 < len(all_cells): # Ensure there's a corresponding value cell
                    value_cell = all_cells[i + 1]
                    label_text = label_cell.get_text(strip=True).lower()
                    details_map[label_text] = value_cell.get_text(strip=True)

            # Populate details dictionary using the lookup map
            details['engine_cc'] = details_map.get("engine (cc)", "")
            details['yom'] = details_map.get("yom", "")
            details['post_make'] = details_map.get("make", "") # "make" from post page, differentiate if needed
            details['model'] = details_map.get("model", "")
            details['detail_price'] = details_map.get("price", "")
            details['gear'] = details_map.get("gear", "")
            details['fuel_type'] = details_map.get("fuel type", "")

        except Exception as e:
            logger.error(f"Error extracting details from post {post_url}: {e}", exc_info=True)
        return details