import tomllib
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

archive_path = ""
feed_directory = ""
feed_url = ""
feeds = []
ratelimit = 0

def generate_config(path):
    logger.info("Generating scrape23 configuration...")
    script_dir = Path(__file__).resolve().parent
    shutil.copy(f"{script_dir}/scrape23.toml.sample")


def load_config(configfile):
    global archive_path
    global feed_directory
    global feed_url
    global feeds
    global ratelimit
    logger.info(f"Loading scrape23 configuration from {configfile}...")
    
    data = []
    try:
        with open(configfile, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file {configfile} not found.")
        exit(1)
    
    archive_path = data['common']['archivepath']
    feed_directory = data['common']['feeddir']
    feed_url = data['common']['feedurl']
    ratelimit = data['common']['ratelimit']
    
    feeds = data['feeds']
    
    logger.info(f"Archive path: {archive_path}, Feed directory: {feed_directory}, Feed base URL: {feed_url}")
    for f in feeds:
        logger.info(f"Feed: {f}")
    
    
