import sqlite3
from .config import DB_PATH
from .utils import setup_logging

logger = setup_logging()

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self.create_table()

    def _connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to DB: {self.db_path}")

    def create_table(self):
        self._connect()
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                make TEXT,
                type TEXT,
                title TEXT,
                location TEXT,
                mileage TEXT,
                overview_price TEXT,
                detail_price TEXT,
                engine_cc TEXT,
                yom TEXT,
                post_make TEXT,
                model TEXT,
                gear TEXT,
                fuel_type TEXT,
                post_url TEXT UNIQUE,
                image_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self.conn.commit()
            logger.info("Listings table ensured.")
        except sqlite3.Error as e:
            logger.critical(f"Error creating listings table: {e}")
            raise

    def insert_listings_batch(self, listings_data):
        if not listings_data:
            return 0
        self._connect()
        data_tuples = [(
            d.get('date', ''), d.get('make', ''), d.get('type', ''),
            d.get('title', ''), d.get('location', ''), d.get('mileage', ''),
            d.get('overview_price', ''), d.get('detail_price', ''),
            d.get('engine_cc', ''), d.get('yom', ''), d.get('post_make', ''),
            d.get('model', ''), d.get('gear', ''), d.get('fuel_type', ''),
            d.get('post_url', ''), d.get('image_url', '')
        ) for d in listings_data]

        try:
            self.cursor.executemany("""
            INSERT OR IGNORE INTO listings (
                date, make, type, title, location, mileage,
                overview_price, detail_price, engine_cc, yom,
                post_make, model, gear, fuel_type, post_url, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data_tuples)
            self.conn.commit()
            inserted = self.cursor.rowcount
            logger.info(f"Inserted {inserted} new listings.")
            return inserted
        except sqlite3.Error as e:
            logger.error(f"DB insert error: {e}")
            self.conn.rollback()
            return 0

    def get_all_post_urls(self):
        self._connect()
        try:
            self.cursor.execute("SELECT post_url FROM listings")
            urls = {row[0] for row in self.cursor.fetchall() if row[0]}
            return urls
        except sqlite3.Error as e:
            logger.error(f"Error fetching URLs: {e}")
            return set()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("DB connection closed.")
            self.conn = None
            self.cursor = None

    def __del__(self):
        self.close()
