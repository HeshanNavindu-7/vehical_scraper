# src/utils.py
import logging
from urllib.parse import urljoin
import os

# --- Logging Setup ---
def setup_logging(level_str=None):
    """
    Sets up logging for the application.
    Reads log level from environment variable LOG_LEVEL if available.
    """
    if level_str is None:
        level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()

    log_level = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() # Output to console
        ]
    )
    return logging.getLogger("vehicle_scraper")

# --- URL Helper ---
def safe_urljoin(base, url):
    """
    Safely joins a base URL with a relative URL.
    Handles various relative URL formats.
    """
    return urljoin(base, url)

# --- Conditional TQDM for Progress Bars ---
# TQDM is enabled/disabled based on the ENABLE_TQDM environment variable.
# This is useful for development (with progress bars) vs. production (cleaner logs).
if os.environ.get('ENABLE_TQDM', 'false').lower() == 'true':
    from tqdm import tqdm as _tqdm
else:
    # Dummy tqdm class that does nothing when disabled
    class _tqdm(object):
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args, **kwargs):
            pass
        def update(self, *args, **kwargs):
            pass

tqdm = _tqdm