import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os

from src.db_manager import DatabaseManager
from src.riyasewana_scraper import RiyasewanaScraper
from src.utils import setup_logging

logger = setup_logging()

path=os.path.join("drivers","chromedriver-linux64","chromedriver")

def setup_driver():
    options = webdriver.ChromeOptions()

    # No need to specify binary_location unless you use a custom browser binary (like a custom Chrome installation)
    # options.binary_location = "C:\\Path\\To\\chrome.exe"

    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--log-level=3')
    
    # Point to your chromedriver.exe directly
    service = Service(path)

    return webdriver.Chrome(service=service, options=options)

def run():
    driver = None
    db_manager = None
    try:
        driver = setup_driver()
        db_manager = DatabaseManager()
        scraper = RiyasewanaScraper(driver=driver, db_manager=db_manager)

        logger.info("Starting Riyasewana scraping job...")
        new_listings = scraper.scrape_site()
        logger.info(f"Scraping job finished. {len(new_listings)} new listings collected.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed.")
        if db_manager:
            db_manager.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    load_dotenv()
    run()
