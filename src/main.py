# src/main.py
import os
import schedule
import time
import subprocess # Retained for the `schedule` library example, not for Cloud Run

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv # For loading environment variables from .env

from .db_manager import DatabaseManager # Dependency Injection for DB
from .riyasewana_scraper import RiyasewanaScraper # Strategy Pattern: Concrete Scraper
# from .ikman_scraper import IkmanScraper # Future Strategy: Another Concrete Scraper
from .utils import setup_logging # Utility for logging
from .config import DB_PATH # Configuration for DB path

logger = setup_logging() # Initialize logger for the main script

def run_scraping_job():
    """
    The main function to orchestrate the daily scraping process.
    It initializes the WebDriver and DatabaseManager, then runs all
    configured site scrapers.
    """
    logger.info("Starting scheduled scraping job.")

    # --- Setup WebDriver (Dependency) ---
    # WebDriver is initialized once and passed to all scrapers.
    # This avoids redundant browser launches and resource overhead.
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')          # Run Chrome without a UI
    options.add_argument('--no-sandbox')        # Required for running in Docker
    options.add_argument('--disable-dev-shm-usage') # Overcomes limited resource problems in Docker
    options.add_argument('--disable-gpu')       # Recommended for headless environments
    options.add_argument('--window-size=1920,1080') # Set a consistent window size for rendering
    options.add_argument('--log-level=3')       # Suppress verbose ChromeDriver logging (INFO, WARNING, ERROR)

    driver = None
    db_manager = None
    try:
        logger.info("Initializing ChromeDriver...")
        # ChromeDriverManager automatically downloads and manages the correct ChromeDriver version
        service = Service(ChromeDriverManager().install()) 
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("ChromeDriver initialized successfully.")

        # --- Initialize Database Manager (Dependency) ---
        # The DatabaseManager is instantiated once and manages the single DB connection.
        db_manager = DatabaseManager(db_path=DB_PATH)

        # --- Initialize and Run Scrapers (Strategy Pattern in action) ---
        # A list of scraper instances, each implementing the ISiteScraper interface.
        # This allows easily adding or removing scraping targets.
        scrapers = [
            RiyasewanaScraper(driver=driver, db_manager=db_manager),
            # IkmanScraper(driver=driver, db_manager=db_manager) # Uncomment when IkmanScraper is ready
        ]

        for scraper in scrapers:
            logger.info(f"Running scraper for: {scraper.__class__.__name__}")
            scraped_data = scraper.scrape_site() # Call the polymorphic scrape_site method
            logger.info(f"Scraper {scraper.__class__.__name__} completed. Processed {len(scraped_data)} new listings.")

    except Exception as e:
        logger.critical(f"A critical error occurred during the scraping job: {e}", exc_info=True)
    finally:
        # --- Resource Cleanup ---
        # Ensure WebDriver and database connections are always closed, even if errors occur.
        if driver:
            driver.quit()
            logger.info("WebDriver quit.")
        if db_manager:
            db_manager.close()
            logger.info("Database connection closed.")
        logger.info("Scraping job finished.")

if __name__ == "__main__":
    # Load environment variables from .env file (for local runs)
    load_dotenv() 

    # --- Execution Modes ---
    # Choose ONE of the following options based on your deployment strategy:

    # Option 1: For local development/testing (run once immediately)
    # This is suitable for debugging the scraping logic.
    run_scraping_job()

    # Option 2: For local scheduling using the `schedule` library
    # This is less ideal for production Docker/Cloud environments as the `schedule`
    # library runs within the container, which might not be reliable or scalable.
    # Instead, external schedulers like GCP Cloud Scheduler or Linux cron jobs are preferred.
    
    # logger.info("Scheduler started. Next run scheduled for 10:00 AM.")
    # schedule.every().day.at("10:00").do(run_scraping_job) # Schedule for 10 AM daily
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60) # Check for pending jobs every minute

    # Option 3: Designed for Docker/Cloud Run where an external scheduler
    # (like GCP Cloud Scheduler) will trigger the Docker container.
    # In this scenario, the Docker container's CMD will simply execute `main.py`
    # which in turn calls `run_scraping_job()` once. The external scheduler
    # handles the daily 10 AM trigger.
    # The `scripts/run_daily_scraper.sh` will call this `main.py` directly.
    pass # No code needed here if using Option 3, as run_scraping_job() is called above.