import config
#from config import archive_path, feed_directory, feed_url
import yt_dlp
import generss
from pathlib import Path
import os
import sys
import argparse
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
import logging
from lxml import etree
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
import email.utils
from humanfriendly import parse_size
import croniter
from time import sleep
import time
import signal
from threading import Event
import pytz


# Logging setup and defaults
sh = logging.StreamHandler()
sf = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
sf.converter = time.localtime
sh.setFormatter(sf)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
for h in logger.handlers:
    logger.removeHandler(h)
logger.addHandler(sh)

 
 
class Feed:
    def __init__(self, name: str, url: str, feedtitle: str, schedule: str, match_title: str|None = None):
        self.name : str = name
        self.url : str = url
        self.match_title : str | None = match_title
        self.cron : croniter.croniter = croniter.croniter(schedule, datetime.now(config.timezone))
        self.next_run: datetime = datetime.fromtimestamp(self.cron.get_next(), config.timezone)
        logger.debug(f"Next run for feed {self.name} is at {self.next_run}.")
        self.feedtitle : str = feedtitle


## service signal handling
quit = Event()
def signal_handler(sig, frame):
    global quit
    logger.info("Signal received, exiting.")
    quit.set()

 
# setup everything so scrape23 will actually work. This will obvs not configure your web server
def initialize_environment():

    logger.info("Checking/initializing environment for scrape23: archive path is " + config.archive_path + ", feed directory is " + config.feed_directory)

    archive = Path(config.archive_path)
    feeds = Path(config.feed_directory)

    
    #Make sure there's a directory for the archive files and create it if it doesn't exist
    if not Path.exists(archive):
        Path.mkdir(archive)
    elif not Path.is_dir(archive):
        logger.error("Archive path is not a directory.")
        return False
    
    # check that archive path is writeable
    checkfile = Path(config.archive_path + '/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        logger.error("Could not write to archive path.")
        return False
    Path.unlink(checkfile)

    #Make sure there's a directory for the feeds
    if not Path.exists(feeds):
        Path.mkdir(feeds)
    elif not Path.is_dir(feeds):
        logger.error("Feed directory is not a directory.")
        return False
    
    # check that feed directory is writeable
    checkfile = Path(config.feed_directory + '/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        logger.error("Could not write to feed directory.")
        return False
    Path.unlink(checkfile)
    
    #check media directory exists
    media = Path(config.feed_directory + '/media')
    if not Path.exists(media):
        Path.mkdir(media)
    elif not Path.is_dir(media):
        logger.error("Media directory is not a directory.")
        return False
    
    # check that media directory is writeable
    checkfile = Path(config.feed_directory + '/media/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        logger.error("Could not write to media directory.")
        return False
    Path.unlink(checkfile)
    
    #check that the thumbnails directory exists
    thumbnails = Path(config.feed_directory + '/thumbnails')
    if not Path.exists(thumbnails):
        Path.mkdir(thumbnails)
    elif not Path.is_dir(thumbnails):
        logger.error("Thumbnails directory is not a directory.")
        return False
    
    #check that the thumbnails directory is writeable
    checkfile = Path(config.feed_directory + '/thumbnails/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        logger.error("Could not write to thumbnails directory.")
        return False
    Path.unlink(checkfile)
        
    return True
    
refresh_thumbnails = False

# get feed thumbnail
def get_thumbnail(url, thumbnail_path):
    ytdl_opts = {
        'writethumbnail': True,
        'skipdownload': True,
        'outtmpl': f"{thumbnail_path}",
        'playlistend': 0,
        'quiet': True
    }
    
    logger.info(f"Getting thumbnail for {url}, saving to {thumbnail_path}")
    urls = [url]
    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        error_code = ytdl.download(urls)
    

    
# initialize a feed and download the episode list for the archive.
def check_archive(feed: Feed, refresh_thumbnails: bool = False):
    logger.info(f"Checking archive for {feed.name}.")
    url =feed.url

    archive = Path(f"{config.archive_path}/{feed.name}.archive")
    
    
    thumbnailpath = Path(f"{config.feed_directory}/thumbnails/{feed.name}.jpg")
    logger.debug(f"Thumbnail path: {thumbnailpath}")
    
    # check episode path
    episodespath = Path(config.feed_directory + '/media/' + feed.name)
    if not Path.exists(episodespath):
        Path.mkdir(episodespath)
    elif not Path.is_dir(episodespath):
        logger.error("Error: episodes path is not a directory.")
        return False
    
    # get feed thumbnail
    if not Path.exists(thumbnailpath) or refresh_thumbnails:
        get_thumbnail(url, thumbnailpath)
    
    # set up ytdl options for archive population
    ytdl_opts = {
        'download_archive': archive,
        'extract_flat': True,
        'force_write_download_archive': True,
        'quiet': True
    }
    
    # use yt_dlp to get a list of past episodes that we don't want to download
    if not Path.exists(archive):
        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
            logger.info(f"Populating archive for {feed.name}.")
            error_code = ytdl.download(url)
    
    return True

def get_episodes(feed: Feed, ratelimit: str|None=None):
    feed_directory = config.feed_directory
    feed_url = config.feed_url
    archive_path = config.archive_path
    
    logger.info(f"Getting episodes for {feed.name}")
    url = feed.url
    logger.debug(f"Feed URL: {url}")
    
    archive = Path(f"{archive_path}/{feed.name}.archive")
    logger.debug(f"Archive path: {archive}")
        
    # check episode path
    episodespath = Path(feed_directory + '/media/' + feed.name)
    if not Path.exists(episodespath):
        Path.mkdir(episodespath)
    elif not Path.is_dir(episodespath):
        logger.error("Episodes path is not a directory.")
        return False
    
    daterange = yt_dlp.utils.DateRange("today-2months", "today")
    
    # set up ytdl options
    ytdl_opts = {
        'ratelimit' : ratelimit,
        'daterange': daterange,
        'download_archive': archive,
        'outtmpl': f"{episodespath}/%(timestamp)s-%(id)s.%(ext)s",
        'extractaudio' : True,
        'audioformat' : 'mp3',
        'ignoreerrors' : True,
        'final_ext': 'mp3',
        'format': 'bestaudio/best',
        'source_address': '0.0.0.0',
        'postprocessors': [{'key': 'FFmpegExtractAudio',
                            'nopostoverwrites': False,
                            'preferredcodec': 'mp3',
                            'preferredquality': '5'},
                            {'add_chapters': True,
                            'add_infojson': 'if_exists',
                            'add_metadata': True,
                            'key': 'FFmpegMetadata'},
                            {'key': 'FFmpegConcat',
                            'only_multi_video': True,
                            'when': 'playlist'}]
    }
    
    if feed.match_title:
        ytdl_opts['matchtitle'] = feed.match_title
    
    # use yt_dlp to get a list of past episodes
    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        error_code = ytdl.download(url)
    return True

# postprocess RSS feed to update publication dates from episode metadata.
def postprocess_rss(feed: Feed):
    
    logger.info(f"Postprocessing RSS for {feed.name}.")
    
    feed_directory = config.feed_directory
    filesdirectory = feed_directory + f'/media/{feed.name}'
    outputfile = f'{feed.name}.rss'
    rsspath = Path(f"{feed_directory}/{outputfile}")
    logger.debug(f"RSS path: {rsspath}")
    
    tree = etree.parse(rsspath)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')
    for item in items:

        # get the filename from the enclosure tag
        enclosure = item.find('enclosure')
        url = enclosure.get('url')
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        file = filesdirectory + '/' + filename
        
        # get the pubdate from MP3 metadata
        mtg = MP3(file)
        date_str = str(mtg.tags['TDRC'])
        title_str = str(mtg.tags['TIT2'])    
        logger.debug(f"File: {filename}, date string: {date_str}")
        dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                
        # get the pubdate tag
        pubdate = item.find('pubDate')
        
        #rewrite pubdate tag
        pubdate.text = email.utils.format_datetime(dt)

    #write out modified RSS file
    logger.debug(f"Writing RSS feed to {rsspath}.")
    tree.write(rsspath, encoding='utf-8', xml_declaration=True) 

#generate RSS
def generate_rss(feed: Feed):
    feed_directory = config.feed_directory
    feed_url = config.feed_url
    
    logger.info(f"Generating RSS feed for {feed.name}.")
    logger.debug(f"Feed title: {feed.feedtitle}")
    filesdirectory = f'media/{feed.name}'
    logger.debug(f"Files directory: {filesdirectory}")
    outputfile = f'{feed.name}.rss'
    logger.debug(f"Output file: {outputfile}")
    thumbnail = f'thumbnails/{feed.name}.jpg'
    logger.debug(f"Thumbnail path: {thumbnail}")
    
    # arguments for genRSS    
    argv = ['-t', feed.feedtitle, '-d', filesdirectory, '-o', outputfile, '-H', feed_url, '-M', '-C', '-e', 'mp3', '-i', thumbnail]

    # push working directory. GenRSS operates on the working directory so we need to change directories.
    cwd = os.getcwd()
    os.chdir(feed_directory)

    logger.debug(f"Executing genRSS in {feed_directory}.")
    
    # run genRSS
    generss.main(argv)

    # pop back to the original working directory
    os.chdir(cwd)
    
    return True

# clean up metadata from the media files for a given feed. This is mostly done for the CTOC:toc stripping
def preprocess_metadata(feed: Feed):
    logger.info(f"Metadata cleanup for feed {feed.name}.")    

    # strip CTOC:toc from all files
    filedir = Path(config.feed_directory + '/media/' + feed.name)
    for f in filedir.iterdir():    
        if f.is_file() and f.suffix == '.mp3':
            logger.debug(f"Checking file {f}.")
            strip_toc(f)
    
    return True

# DTOC:toc ID3 tags break eye3d library used by genRSS, so let's strip those out.
def strip_toc(f):
    if f.is_file():
        mtgfile = ID3(f) 
        if 'CTOC:toc' in mtgfile:
            logger.info(f"Stripping CTOC:toc from {f}")
            mtgfile.pop('CTOC:toc')
        mtgfile.save()

# Process a single feed
def process_feed(feed: Feed, now: datetime|None, no_download=False):
    logger.debug(f"Processing feed {feed.name}.")
    
    if now is not None:
        if feed.next_run > now:
            logger.debug(f"Skipping {feed.name}, next run at {feed.next_run}.")
            return True
        else:
            # update next run
            feed.next_run = datetime.fromtimestamp(feed.cron.get_next())
            logger.debug(f"Next run for feed {feed.name} updated to {feed.next_run}.")

    if not check_archive(feed, refresh_thumbnails):
        return False

    if not no_download:
        get_episodes(feed)

    else:
        logger.info(f"Skipping episode downloads for {feed.name}.")
    
    # filter MP3's            
    preprocess_metadata(feed)
    #generate RSS
    generate_rss(feed)
    # postprocess RSS file
    postprocess_rss(feed)


# main function. Parse arguments and configuration and run all phases for each feed
def main(argv=None):
    
    parser = argparse.ArgumentParser(description='Scrape23 turns any YouTube channel into an audio podcast.')
    parser.add_argument('--initialize', action='store_true', default=False,
                      help='Check that all necessary filesystem locations exist and are writeable.', dest='initialize')
    parser.add_argument('--initialize-archives', action='store_true', default=False,
                      help='Initialize archives without downloading any episodes.', dest='initialize_archives')
    parser.add_argument('--refresh-thumbnails', action='store_true', default=False,
                      help='Refresh thumbnails', dest='refresh_thumbnails')
    parser.add_argument('--feed', action='store',
                      help='Feed to scrape', dest='feed')
    parser.add_argument('--config', action='store', default='~/scrape23.toml', dest='config',
                        help='Configuration file to use')
    parser.add_argument('--no-download', action='store_true', default=False,
                        help='Do not download any episodes, only process files and generate RSS', dest='no_download')
    parser.add_argument('--log', action='store', default='/var/log/scrape23.log',
                        help='Specify log file', dest='log_path')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug logging', dest='debug')
    #TODO: ADD IMPLEMENTATION FOR THIS
    #parser.add_argument('--ignore-datelimit', action='store_true', default=False,
    #                    help='Ignore the two month hard limit on episode age.', dest='ignore_datelimit')
    parser.add_argument('--ratelimit', action='store', default=None,
                        help='Rate limit for YouTube downloads. This can be also used to overide the rate limit specified in the config file. Use kB, MB, etc. for bytes per second, kb, Mb, etc. for bits.', dest='ratelimit')
    parser.add_argument('--ignore-ratelimit', action='store_true', default=False,
                        help='Ignore the rate limit specified in the config file.', dest='ignore_ratelimit')
    
    args = parser.parse_args(argv)
    
    #logging is critical for other things, so let's set it up first
    if args.log_path:
        fh = logging.FileHandler(args.log_path)
        ff = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        fh.setFormatter(ff)
        logger.addHandler(fh)
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging.")
    
    # get configuration
    config.load_config(args.config)
    
    feeds: list[Feed] = []
    
    for feedname in config.feeds:
        logger.info(f"Loading feed: {feedname}")
        feeds.append(Feed(feedname, 
                          config.feeds[feedname]['url'],
                          config.feeds[feedname]['feedtitle'],
                          config.feeds[feedname]['schedule'],
                          config.feeds[feedname].get('match_title', None)))
    
    #set the rate limit
    ratelimit = None 
    # If ratelimit is specified...
    if args.ratelimit is not None:
        try:
            logger.info(f"Rate limit: {args.ratelimit}")
            ratelimit = parse_size(args.ratelimit)
        except:
            logger.error(f"Error: {args.ratelimit} is not a valid rate limit.")
            return False
    else:
        # If not, get value from config
        ratelimit = config.ratelimit
        if ratelimit:
            logger.debug(f"Rate limit: {args.ratelimit}")
            
    # if told to ignore ratelimit, Leeroy Jenkins it
    if args.ignore_ratelimit:
        ratelimit = None
        logger.info("Force ignore ratelimit.")
    
    
    if args.initialize:
        if not initialize_environment():
            return False

    # initialize archives.    
    if args.initialize_archives:
        for feed in feeds:
            if not check_archive(feed):
                return False
            return True

    refresh_thumbnails = args.refresh_thumbnails
    
    # at this point configuration is done, it's time to do the actual work.
    
    # check if we want to manually process a particular feed
    if args.feed:
        logger.info(f"Processing feed {args.feed}")
        feed = next((f for f in feeds if f.name == args.feed), None)
        if feed is None:
            logger.error(f"Feed {args.feed} not configured.")
            return False
        process_feed(feed, None, args.no_download)
        return True
    
    ## Default behaviour is to process all feeds from the config file and then follow the croniter schedule.
    logger.info("Running in service mode.")

    # Register signal handler for SIGTERM in service mode
    signal.signal(signal.SIGTERM, signal_handler)
    # run every 5 minutes    
    wait_cron = croniter.croniter("*/5 * * * *")
    
    # service mode main loop       
    while not quit.is_set():
        now: datetime = datetime.now(config.timezone)

        logger.debug(f"Current time: {now}.")
        for feed in feeds:
            process_feed(feed, now, args.no_download)    
        
        next_run: datetime = datetime.fromtimestamp(wait_cron.get_next(), config.timezone)

        # sleep until next run
        logger.debug(f"Next run at {next_run}.")
        quit.wait((next_run - now).total_seconds())

    return True

# Default entrypoint
if __name__ == "__main__":
    main(sys.argv)