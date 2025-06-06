import time
import random
from typing import List, Dict
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from dateutil.parser import parse
from .config import (
    RIYASWANA_BASE_URL, RIYASWANA_VEHICLE_TYPES, RIYASWANA_VEHICLE_MAKES,
    DELAY_RANGE_PAGE_LOAD_SEC, DELAY_RANGE_POST_LOAD_SEC, DB_BATCH_INSERT_SIZE
)
from .utils import safe_urljoin, setup_logging
from .interfaces import ISiteScraper

logger = setup_logging()

class RiyasewanaScraper(ISiteScraper):
    def __init__(self, driver: WebDriver, db_manager):
        self.driver = driver
        self.db_manager = db_manager
        self.base_url = RIYASWANA_BASE_URL
        self.vehicle_types = RIYASWANA_VEHICLE_TYPES
        self.vehicle_makes = RIYASWANA_VEHICLE_MAKES
        self.delay_page = DELAY_RANGE_PAGE_LOAD_SEC
        self.delay_post = DELAY_RANGE_POST_LOAD_SEC
        self.batch_size = DB_BATCH_INSERT_SIZE
        self.seen_urls = set(db_manager.get_all_post_urls())
        logger.info(f"Loaded {len(self.seen_urls)} URLs from DB.")

    def _parse_listing_date(self, date_str: str) -> datetime:
        try:
            # Attempt to parse the date string
            return parse(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def scrape_site(self) -> List[Dict]:
        all_new_listings = []
        current_batch = []

        total_iterations = len(self.vehicle_types) * len(self.vehicle_makes)
        with tqdm(total=total_iterations, desc="Riyasewana Types x Makes") as pbar_outer:
            for make in self.vehicle_makes:
                for vehicle_type in self.vehicle_types:
                    logger.info(f"Scraping Type='{vehicle_type}', Make='{make}'")
                    page = 1
                    while True:
                        url = f"{self.base_url}/search/{vehicle_type}/{make}"
                        if page > 1:
                            url += f"?page={page}"
                        logger.info(f"Loading page {page}: {url}")

                        try:
                            self.driver.get(url)
                            time.sleep(random.uniform(*self.delay_page))
                            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                            content_div = soup.find('div', id='content')
                            ul_tag = content_div.find('ul') if content_div else None
                            if not ul_tag:
                                logger.info("No listings container found, stopping pagination.")
                                break

                            li_tags = ul_tag.find_all('li', class_="item round")
                            if not li_tags:
                                logger.info("No listings found on page, stopping pagination.")
                                break

                            new_on_page = 0

                            for li in li_tags:
                                overview = self._extract_listing_details(li)
                                post_url = overview.get('post_url', '')
                                if not post_url or post_url in self.seen_urls:
                                    continue

                                # Parse and filter by date (last 7 days)
                                listing_date_str = overview.get('date', '')
                                listing_date = self._parse_listing_date(listing_date_str)

                                if listing_date is None:
                                    logger.info(f"Skipping listing with unparseable date: {listing_date_str}")
                                    continue

                                if listing_date < datetime.now() - timedelta(days=1):
                                    logger.info(f"Skipping old listing dated {listing_date_str}")
                                    continue

                                self.seen_urls.add(post_url)

                                details = self._extract_post_details(post_url)

                                combined = {**overview, **details,
                                            'make': make, 'type': vehicle_type}

                                all_new_listings.append(combined)
                                current_batch.append(combined)
                                new_on_page += 1

                                if len(current_batch) >= self.batch_size:
                                    self.db_manager.insert_listings_batch(current_batch)
                                    current_batch.clear()

                            if new_on_page == 0:
                                logger.info("No new listings on this page, ending pagination.")
                                break

                            page += 1
                        except Exception as e:
                            logger.error(f"Error scraping page {page}: {e}", exc_info=True)
                            break
                    pbar_outer.update(1)

        if current_batch:
            self.db_manager.insert_listings_batch(current_batch)

        logger.info(f"Scraping completed, total new listings: {len(all_new_listings)}")
        return all_new_listings

    def _extract_listing_details(self, li_tag) -> Dict:
        data = {}
        try:
            a_tag = li_tag.select_one('h2.more a')
            data['title'] = a_tag.text.strip() if a_tag else ""
            post_url_raw = a_tag['href'] if a_tag and 'href' in a_tag.attrs else ""
            data['post_url'] = post_url_raw if post_url_raw.startswith("http") else safe_urljoin(self.base_url, post_url_raw)

            img_tag = li_tag.select_one('div.imgbox a img')
            img_src = img_tag['src'].strip() if img_tag and 'src' in img_tag.attrs else ""
            data['image_url'] = img_src if img_src.startswith("http") else "https:" + img_src if img_src else ""

            date_div = li_tag.find('div', class_='boxintxt s')
            data['date'] = date_div.text.strip() if date_div else ""

            data['location'] = ""
            data['overview_price'] = ""
            data['mileage'] = ""

            boxintxts = li_tag.find_all('div', class_='boxintxt')
            for box in boxintxts:
                txt = box.text.strip()
                if "km" in txt.lower():
                    data['mileage'] = txt
                elif "rs" in txt.lower() or "negotiable" in txt.lower():
                    data['overview_price'] = txt
                elif txt not in [data['overview_price'], data['mileage'], data['date']]:
                    data['location'] = txt
        except Exception as e:
            logger.warning(f"Error extracting listing overview: {e}")
        return data

    def _extract_post_details(self, post_url: str) -> Dict:
        details = {}
        try:
            self.driver.get(post_url)
            time.sleep(random.uniform(*self.delay_post))
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            all_cells = soup.select('td.aleft, td.aleft.ftin, td.aleft.tfiv')
            for i in range(0, len(all_cells), 2):
                label = all_cells[i].get_text(strip=True).lower()
                if i + 1 < len(all_cells):
                    value = all_cells[i + 1].get_text(strip=True)
                    details[label] = value

            return {
                'engine_cc': details.get("engine (cc)", ""),
                'yom': details.get("yom", ""),
                'post_make': details.get("make", ""),
                'model': details.get("model", ""),
                'price_detail': details.get("price", ""),
                'gear': details.get("gear", ""),
                'fuel_type': details.get("fuel type", ""),
            }
        except Exception as e:
            logger.error(f"Error extracting post details from {post_url}: {e}", exc_info=True)
            return details
