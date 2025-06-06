import os

RIYASWANA_BASE_URL = "https://riyasewana.com"
DB_PATH = os.path.join(os.getcwd(), "riyasewana.db")

RIYASWANA_VEHICLE_TYPES = ['cars']
RIYASWANA_VEHICLE_MAKES = ['volvo']

DELAY_RANGE_PAGE_LOAD_SEC = (2, 5)
DELAY_RANGE_POST_LOAD_SEC = (2, 4)

DB_BATCH_INSERT_SIZE = 50
