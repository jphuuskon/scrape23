import tomllib
import logging

logger = logging.getLogger(__name__)

archive_path = ""
feed_directory = ""
feed_url = ""
feeds = []


def load_config(configfile="./scrape23.toml"):
    global archive_path
    global feed_directory
    global feed_url
    global feeds
    logger.info("Loading scrape23 configuration...")
    
    data = []
    with open(configfile, "rb") as f:
        data = tomllib.load(f)
    
    archive_path = data['common']['archivepath']
    feed_directory = data['common']['feeddir']
    feed_url = data['common']['feedurl']
    feeds = data['feeds']
   
    logger.info(f"Common configuration: Archive path: {archive_path}, Feed directory: {feed_directory}, Feed base URL: {feed_url}")
    for f in feeds:
        logger.info(f"Configured feed: {f}")
    
    
