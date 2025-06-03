# src/config.py
import os

# --- General Configuration ---
# Database path: Using os.getcwd() to ensure it's relative to the project root
# when run from the main script, or /app in Docker.
DB_PATH = os.path.join(os.getcwd(), "riyasewana.db") 

# --- Riyasewana Specific Configuration ---
RIYASWANA_BASE_URL = "https://riyasewana.com"

RIYASWANA_VEHICLE_TYPES = ['cars', 'vans', 'suvs', 'crew-cabs', 'pickups']
RIYASWANA_VEHICLE_MAKES = ['toyota', 'nissan', 'suzuki', 'micro', 'mitsubishi', 'mahindra', 'mazda', 'daihatsu', 'hyundai', 'kia', 'bmw', 'perodua', 'tata']

# CSS Selectors for Riyasewana.com
# IMPORTANT: These selectors are examples. You MUST verify them by inspecting
# the actual website's HTML as websites frequently update their structure.
RIYASWANA_SELECTORS = {
    'LISTING_CONTAINER': 'li.item.round',
    'LISTING_TITLE_LINK': 'h2 a',
    'LISTING_IMAGE': 'img',
    'LISTING_DATE': 'div.boxintxt.s',
    'LISTING_BOX_TEXTS': 'div.boxintxt', # Used for mileage, location, price
    'POST_DETAIL_TABLE_CELLS': 'td.aleft, td.aleft.ftin, td.aleft.tfiv', # For detail page table
    'PAGINATION_NEXT_BUTTON': 'a.next' # Example for robust pagination (not fully implemented in scraper for brevity)
}

# --- Scraping Delays (to be polite and avoid blocks) ---
DELAY_RANGE_PAGE_LOAD_SEC = (2, 5) # Random delay between loading main listing pages
DELAY_RANGE_POST_LOAD_SEC = (2, 4) # Random delay before extracting details from an individual post page

# --- Database Settings ---
DB_BATCH_INSERT_SIZE = 50 # Number of listings to insert into the DB in one batch operation