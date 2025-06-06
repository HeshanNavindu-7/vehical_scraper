import logging
import os
from urllib.parse import urljoin

def setup_logging(level_str=None):
    level_str = level_str or os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("vehicle_scraper")

def safe_urljoin(base, url):
    return urljoin(base, url)

if os.environ.get('ENABLE_TQDM', 'false').lower() == 'true':
    from tqdm import tqdm as _tqdm
else:
    class _tqdm:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def update(self, *args): pass

tqdm = _tqdm
