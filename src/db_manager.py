# src/db_manager.py
import sqlite3
import os
from .utils import setup_logging
from .config import DB_PATH

logger = setup_logging()

class DatabaseManager:
    """
    Manages all interactions with the SQLite database.
    Applies Encapsulation by hiding database connection details and
    centralizing all SQL operations.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect() # Establish connection on initialization
        self.create_table() # Ensure table exists

    def _connect(self):
        """
        Establishes a connection to the database if one is not already open.
        This internal method ensures the connection is always ready for operations.
        """
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
                logger.info(f"Connected to database: {self.db_path}")
            except sqlite3.Error as e:
                logger.critical(f"Error connecting to database {self.db_path}: {e}")
                raise # Re-raise to halt execution if DB connection fails

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Database connection closed.")

    def create_table(self):
        """
        Creates the 'listings' table if it doesn't already exist.
        Includes a 'created_at' timestamp for tracking.
        """
        self._connect() # Ensure connection is open
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
                post_url TEXT UNIQUE, -- Ensures unique listings based on URL
                image_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Timestamp for when data was scraped
            );
            """)
            self.conn.commit()
            logger.info("Database table 'listings' created/verified successfully.")
        except sqlite3.Error as e:
            logger.critical(f"Error creating table: {e}")
            raise

    def insert_listings_batch(self, listings_data: list[dict]) -> int:
        """
        Inserts a batch of listing data into the database.
        Uses INSERT OR IGNORE to prevent duplicates based on 'post_url'.
        Utilizes `executemany` for efficient bulk insertion within a single transaction.
        
        Args:
            listings_data (list[dict]): A list of dictionaries, each representing a listing.
            
        Returns:
            int: The number of new unique listings actually inserted.
        """
        if not listings_data:
            return 0 # No data to insert

        self._connect()
        inserted_count = 0
        try:
            # Prepare data as a list of tuples in the correct order for executemany
            data_tuples = []
            for data in listings_data:
                data_tuples.append((
                    data.get('date', ''), data.get('make', ''), data.get('type', ''),
                    data.get('title', ''), data.get('location', ''), data.get('mileage', ''),
                    data.get('overview_price', ''), data.get('detail_price', ''),
                    data.get('engine_cc', ''), data.get('yom', ''), data.get('post_make', ''),
                    data.get('model', ''), data.get('gear', ''), data.get('fuel_type', ''),
                    data.get('post_url', ''), data.get('image_url', '')
                ))

            self.cursor.executemany("""
            INSERT OR IGNORE INTO listings (
                date, make, type, title, location, mileage,
                overview_price, detail_price, engine_cc, yom,
                post_make, model, gear, fuel_type, post_url, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data_tuples)
            
            self.conn.commit()
            inserted_count = self.cursor.rowcount # Number of rows actually inserted by the last operation
            logger.info(f"Attempted to insert {len(listings_data)} listings. {inserted_count} new unique listings inserted.")
        except sqlite3.Error as e:
            self.conn.rollback() # Rollback all changes in the batch on error
            logger.error(f"Database error during batch insert: {e}")
        return inserted_count

    def get_all_post_urls(self) -> set[str]:
        """
        Fetches all 'post_url' values from the database.
        Used to initialize the 'seen_urls' set in scrapers to avoid re-processing.
        """
        self._connect()
        try:
            self.cursor.execute("SELECT post_url FROM listings")
            # Filter out None or empty strings from the fetched URLs
            return {row[0] for row in self.cursor.fetchall() if row[0]}
        except sqlite3.Error as e:
            logger.error(f"Error fetching existing post URLs: {e}")
            return set() # Return an empty set on error

    def fetch_all_listings(self) -> list[tuple]:
        """Fetches all listings from the database."""
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM listings")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching all listings: {e}")
            return []

    def __del__(self):
        """
        Destructor to ensure the database connection is closed
        when the DatabaseManager object is garbage collected.
        """
        self.close()