import yt_dlp
import generss
from pathlib import Path
from .config import *
import os
import sys
import argparse

# setup everything so scrape23 will actually work
def initialize_environment():

    print("Initializing environment for scrape23: archive path is " + archive_path + ", feed directory is " + feed_directory)
    #Make sure there's a path for the archive files
    
    archive = Path(archive_path)
    feeds = Path(feed_directory)
    
    if not Path.exists(archive):
        Path.mkdir(archive)
    elif not Path.is_dir(archive):
        print("Error: archive path is not a directory.")
        return False
    
    # check that archive path is writeable
    checkfile = Path(archive_path + '/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        print("Error: could not write to archive path.")
        return False
    Path.unlink(checkfile)

    #Make sure there's a path for the feeds
    if not Path.exists(feeds):
        Path.mkdir(feeds)
    elif not Path.is_dir(feeds):
        print("Error: feed directory is not a directory.")
        return False
    
    # check that feed directory is writeable
    checkfile = Path(feed_directory + '/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        print("Error: could not write to feed directory.")
        return False
    Path.unlink(checkfile)
    
    #check media directory exists
    media = Path(feed_directory + '/media')
    if not Path.exists(media):
        Path.mkdir(media)
    elif not Path.is_dir(media):
        print("Error: media directory is not a directory.")
        return False
    
    # check that media directory is writeable
    checkfile = Path(feed_directory + '/media/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        print("Error: could not write to media directory.")
        return False
    Path.unlink(checkfile)
    
    #check that the thumbnails directory exists
    thumbnails = Path(feed_directory + '/thumbnails')
    if not Path.exists(thumbnails):
        Path.mkdir(thumbnails)
    elif not Path.is_dir(thumbnails):
        print("Error: thumbnails directory is not a directory.")
        return False
    
    #check that the thumbnails directory is writeable
    checkfile = Path(feed_directory + '/thumbnails/scrape23_check')
    try:
        Path.touch(checkfile)
    except:
        print("Error: could not write to thumbnails directory.")
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
    
    print(f"Getting thumbnail for {url}, saving to {thumbnail_path}")
    urls = [url]
    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        error_code = ytdl.download(urls)
    
daterange = yt_dlp.utils.DateRange("today-2months", "today")
    
# initialize a feed
def initialize_archive(feed_name, refresh_thumbnails = False):
    print(f"Initializing archive for {feed_name} - Friendly name: {feeds[feed_name]['feedname']}")
    url =f"{feeds[feed_name]['url']}"
    print(f"Feed URL: {url}")
    
    archive = Path(f"{archive_path}/{feed_name}.archive")
    print(f"Archive path: {archive}")
    
    thumbnailpath = Path(f"{feed_directory}/thumbnails/{feed_name}.jpg")
    print(f"Thumbnail path: {thumbnailpath}")
    
    # check episode path
    episodespath = Path(feed_directory + '/media/' + feed_name)
    if not Path.exists(episodespath):
        Path.mkdir(episodespath)
    elif not Path.is_dir(episodespath):
        print("Error: episodes path is not a directory.")
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

def get_episodes(feed_name):
    print(f"Getting episodes for {feed_name}")
    url = feeds[feed_name]['url']
    print(f"Feed URL: {url}")
    
    archive = Path(f"{archive_path}/{feed_name}.archive")
    print(f"Archive path: {archive}")
        
    # check episode path
    episodespath = Path(feed_directory + '/media/' + feed_name)
    if not Path.exists(episodespath):
        Path.mkdir(episodespath)
    elif not Path.is_dir(episodespath):
        print("Error: episodes path is not a directory.")
        return False
    
    # set up ytdl options
    ytdl_opts = {
        'daterange': daterange,
        'download_archive': archive,
        'outtmpl': f"{episodespath}/%(timestamp)s-%(id)s.%(ext)s",
        'extractaudio' : True,
        'audioformat' : 'mp3',
        'ignoreerrors' : True,
        'final_ext': 'mp3',
        'format': 'bestaudio/best',
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
    
    if feeds[feed_name]['match_title']:
        ytdl_opts['matchtitle'] = feeds[feed_name]['match_title']
    
    # use yt_dlp to get a list of past episodes
    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
        error_code = ytdl.download(url)
    return True

#generate RSS
def generate_rss(feedname):
    print(f"Generating RSS feed for {feedname}")
    feedtitle = feeds[feedname]["feedname"]
    filesdirectory = f'media/{feedname}'
    outputfile = f'{feedname}.rss'
    thumbnail = f'thumbnails/{feedname}.jpg'

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

    generss.main(argv)

    os.chdir(cwd)

    return True

def main(argv=None):
    
    parser = argparse.ArgumentParser(description='Podcast feed scraper and RSS generator')
    parser.add_argument('--initialize', action='store_true', default=False,
                      help='Check that all necessary filesystem locations exist and are writeable.', dest='initialize')
    parser.add_argument('--initialize-archives', action='store_true', default=False,
                      help='Initialize archives without downloading any episodes.', dest='initialize_archives')
    parser.add_argument('--refresh-thumbnails', action='store_true', default=False,
                      help='Refresh thumbnails', dest='refresh_thumbnails')
    parser.add_argument('--feed', action='store', default=None,
                      help='Feed to scrape', dest='feed')

    args = parser.parse_args(argv)
    
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
        if not args.feed in feeds:
            print(f"Error: feed {args.feed} not configured.")
            return False
        feed = args.feed
        if not initialize_archive(feed, refresh_thumbnails):
            return False
        get_episodes(feed)
        generate_rss(feed)
        return True
    
    for feed in feeds:
        if not initialize_archive(feed, refresh_thumbnails):
            return False
        get_episodes(feed)
        generate_rss(feed)
    
    return True

if __name__ == "__main__":
    main(sys.argv)