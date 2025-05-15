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
from datetime import datetime, timezone
import email.utils
from humanfriendly import parse_size

# Logging setup and defaults
logging.basicConfig(format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
sf = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
sh.setFormatter(sf)
logger.setLevel(logging.INFO)
 
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
    
daterange = yt_dlp.utils.DateRange("today-2months", "today")
    
# initialize a feed
def initialize_archive(feed_name, refresh_thumbnails = False):
    feeds = config.feeds
    logger.info(f"Initializing archive for {feed_name} - Friendly name: {feeds[feed_name]['feedname']}")
    url =f"{config.feeds[feed_name]['url']}"
    logger.debug(f"Feed URL: {url}")
    
    archive = Path(f"{config.archive_path}/{feed_name}.archive")
    logger.debug(f"Archive path: {archive}")
    
    if not Path.exists(archive):
        try:
            Path.touch(archive)
        except:
            logger.error("Could not write to archive path.")
            return False
    
    thumbnailpath = Path(f"{config.feed_directory}/thumbnails/{feed_name}.jpg")
    logger.debug(f"Thumbnail path: {thumbnailpath}")
    
    # check episode path
    episodespath = Path(config.feed_directory + '/media/' + feed_name)
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
            error_code = ytdl.download(url)
    
    return True

def get_episodes(feed_name, ratelimit=None):
    feeds = config.feeds
    feed_directory = config.feed_directory
    feed_url = config.feed_url
    archive_path = config.archive_path
    
    logger.info(f"Getting episodes for {feed_name}")
    url = feeds[feed_name]['url']
    logger.debug(f"Feed URL: {url}")
    
    archive = Path(f"{archive_path}/{feed_name}.archive")
    logger.debug(f"Archive path: {archive}")
        
    # check episode path
    episodespath = Path(feed_directory + '/media/' + feed_name)
    if not Path.exists(episodespath):
        Path.mkdir(episodespath)
    elif not Path.is_dir(episodespath):
        logger.error("Episodes path is not a directory.")
        return False
    
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
    
    if 'match_title' in feeds[feed_name]:
        ytdl_opts['matchtitle'] = feeds[feed_name]['match_title']
    
    # use yt_dlp to get a list of past episodes
    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        error_code = ytdl.download(url)
    return True

# postprocess RSS feed to update publication dates from episode metadata.
def postprocess_rss(feedname):
    
    logger.info(f"Postprocessing RSS for {feedname}.")
    
    feeds = config.feeds
    feed_directory = config.feed_directory
    filesdirectory = feed_directory + f'/media/{feedname}'
    outputfile = f'{feedname}.rss'
    rsspath = Path(f"{feed_directory}/{outputfile}")
    logger.debug(f"RSS path: {rsspath}")
    
    
    tree = etree.parse(rsspath)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')
    for item in items:
        # get the filename
        
        enclosure = item.find('enclosure')
        url = enclosure.get('url')
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        file = filesdirectory + '/' + filename
        
        # get the pubdate from inside the mp3
        
        mtg = MP3(file)
        
        date_str = str(mtg.tags['TDRC'])
        title_str = str(mtg.tags['TIT2'])    
        logger.debug(f"Episode name: {title_str}, date string: {date_str}")
        dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        rfc2822_date = email.utils.format_datetime(dt)
        
        # get the pubdate tag
        pubdate = item.find('pubDate')
        
        #rewrite pubdate tag
        pubdate.text = rfc2822_date

    #write out modified RSS feed
    logger.debug(f"Writing RSS feed to {rsspath}.")
    tree.write(rsspath, encoding='utf-8', xml_declaration=True) 

#generate RSS
def generate_rss(feedname):
    feeds = config.feeds
    feed_directory = config.feed_directory
    feed_url = config.feed_url
    
    logger.info(f"Generating RSS feed for {feedname}.")
    feedtitle = feeds[feedname]["feedname"]
    logger.debug(f"Feed title: {feedtitle}")
    filesdirectory = f'media/{feedname}'
    logger.debug(f"Files directory: {filesdirectory}")
    outputfile = f'{feedname}.rss'
    logger.debug(f"Output file: {outputfile}")
    thumbnail = f'thumbnails/{feedname}.jpg'
    logger.debug(f"Thumbnail path: {thumbnail}")
    
    
    argv = ['-t', feedtitle,
            '-d', filesdirectory,
            '-o', outputfile,
            '-H', feed_url,
            '-M',
            '-C',
            '-e', 'mp3',
            '-i', thumbnail]

    cwd = os.getcwd()
    os.chdir(feed_directory)

    logger.debug(f"Executing genRSS in {feed_directory}.")
    
    generss.main(argv)

    os.chdir(cwd)
    
    postprocess_rss(feedname)

    return True

# clean up the metadata from the media files for a given feed. This is mostly done for the CTOC:toc stripping
def filter(feed):
    logger.info(f"Metadata cleanup for feed {feed}.")
    feeds = config.feeds
    if not feed in feeds:
        logger.error(f"Feed {feed} not configured.")
        return False
    
    # strip CTOC:toc from all files
    filedir = Path(config.feed_directory + '/media/' + feed)
    for f in filedir.iterdir():    
        if f.is_file() and f.suffix == '.mp3':
            logger.debug(f"Stripping file {f}.")
            strip_toc(f)
    
    return True

# sTOC:toc ID3 tags break eye3d library used by genRSS, so let's strip those out.
def strip_toc(f):
    if f.is_file():
        mtgfile = ID3(f) 
        if 'CTOC:toc' in mtgfile:
            logger.info(f"Stripping CTOC:toc from {f}")
            mtgfile.pop('CTOC:toc')
        mtgfile.save()


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
    parser.add_argument('--config', action='store', default='./scrape23.toml', dest='config',
                        help='Configuration file to use')
    parser.add_argument('--no-download', action='store_true', default=False,
                        help='Do not download any episodes, only process files and generate RSS', dest='no_download')
    parser.add_argument('--log', action='store', default='/var/log/scrape23.log',
                        help='Specify log file', dest='log_path')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug logging', dest='debug')
    parser.add_argument('--ignore-datelimit', action='store_true', default=False,
                        help='Ignore the two month hard limit on how old episodes to download. Careless usage of this argument may result getting blocked by YouTube.', dest='ignore_datelimit')
    parser.add_argument('--ratelimit', action='store', default=None,
                        help='Rate limit for YouTube downloads. This can be also used to overide the rate limit specified in the config file. Use kB, MB, etc. for bytes per second, kb, Mb, etc. for bits.', dest='ratelimit')
    parser.add_argument('--ignore-ratelimit', action='store_true', default=False,
                        help='Ignore the rate limit specified in the config file.', dest='ignore_ratelimit')
    
    
    args = parser.parse_args(argv)
    
    if args.log_path:
        fh = logging.FileHandler(args.log_path)
        ff = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        fh.setFormatter(ff)
        logger.addHandler(fh)
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging.")
    
    
    
    ratelimit = None 
    # If ratelmit is specified...
    if args.ratelimit:
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
            logger.info(f"Rate limit: {args.ratelimit}")
            
    # if told to ignore ratelimit, Leeroy Jenkins it
    if args.ignore_ratelimit:
        ratelimit = None
        logger.info("Force ignore ratelimit.")
    
    
    config.load_config(args.config)
    feeds = config.feeds
    
    if args.initialize:
        if not initialize_environment():
            return False

        
    if args.initialize_archives:
        for feed in feeds:
            if not initialize_archive(feed):
                return False
            return True

    refresh_thumbnails = args.refresh_thumbnails
    
    if args.feed:
        logger.info(f"Processing feed {args.feed}")
        if not args.feed in feeds:
            logger.error(f"Error: feed {args.feed} not configured.")
            return False
        feed = args.feed
        if not initialize_archive(feed, refresh_thumbnails):
            return False
        get_episodes(feed)
        generate_rss(feed)
        return True
    
    ## Default behaviour is to process all feeds
    ## Starting here:
    
    logger.info("Processing all feeds.")
    
    for feed in feeds:
        logger.info(f"Processing feed {feed}.")
        if not initialize_archive(feed, refresh_thumbnails):
            return False
        if not args.no_download:
            get_episodes(feed)
        else:
            logger.info(f"Skipping episode downloads for {feed}.")
            
        filter(feed)
        
        generate_rss(feed)
        
    return True


# Entrypoint
if __name__ == "__main__":
    main(sys.argv)