import os

RIYASWANA_BASE_URL = "https://riyasewana.com"

RIYASWANA_VEHICLE_TYPES = ['cars']
RIYASWANA_VEHICLE_MAKES = ['volvo']

DELAY_RANGE_PAGE_LOAD_SEC = (2, 5)
DELAY_RANGE_POST_LOAD_SEC = (2, 4)
DB_BATCH_INSERT_SIZE = 50

# DB settings from env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "riyasewana")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")
