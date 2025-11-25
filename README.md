# Scrape23

Scrape23 is a utility to convert any YouTube channel into a podcast feed served from your own web server. It uses yt-dlp to download videos and extract audio to mp3 and genRSS to generate the RSS feed file. 

## What it does
- Turns any Youtube URL into a podcast channel. This can be a @channel or even a search URL, though I recommend you point it to a @channel/videos URL but technically anything that `yt-dlp` accepts is fair game.
- Uses `yt-dlp` to download videos and extract audio tracks into MP3 and `mutagen` to cleanup the MP3 metadata to prevent `genRSS` from crashing and `lxml` to fix the publication dates. One of these days I swear I'll contribute a fix to `genRSS` so that both of these hacks can be dealt with.
- generates the RSS feed file with `genRSS`.

## What it won't do
- scrape23 does not include a web server. You still need to set up a web server such as `Nginx` and configure it yourself.
- scrape23 does not confiugure your web server. You need to configure your webserver to serve the directory where scrape23 puts the feeds and data
- scrape23 does not configure security or access control for the feeds. That is your responsibility.


## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/jphuuskon/scrape23.git
    cd scrape23
    ```

2. Install Poetry if not already installed:
    ```bash
    pip install poetry
    ```

3. Install dependencies and set up the environment:
    ```bash
    poetry install
    ```

4. yt-dlp uses ffmpeg to extract the audio so you might want to ensure you have `ffmpeg` installed:
    ```bash
    sudo apt install ffmpeg
    ```

6. Check the output directories with:
    
    scrape23 --initialize --config yourconfigfile.toml
    ```
7. If you don't want to download every past episode and instead only begin with episodes that will be release in the future you can do that by  initializing the `yt-dlp` archives:
    ```bash
    scrape23 --initialize-archives --config yourconfigfile.toml
    ```

7. Add scrape23 to your crontab. This example runs scrape23 five minutes past the hour every three hours:
    ```
    5 */3 * * *  scrape23 --config yourconfigfile.toml
    ```

8. Subscribe to your feeds on your podcast client.

## Configuration

Configuration options are documented in `scrape23.toml.sample`.


## Calling scrape23 manually

You can execute scrape23 manually by just calling:
```bash
scrape23
```

## Command Line Options

Scrape23 provides several command line options to control its behavior:

### Basic Usage
```bash
scrape23 [OPTIONS]
```

### Configuration
- `--config CONFIG_FILE`  
  Specify the configuration file to use. If not provided, scrape23 will look for `~/scrape23.toml`.

### Initialization Options
- `--initialize`  
  Check that all necessary filesystem locations exist and are writeable. Use this to set up your environment before first run.

- `--initialize-archives`  
  Initialize archives without downloading any episodes. This populates the download archive with existing episodes so only future episodes will be downloaded.

### Feed Processing
- `--feed FEED_NAME`  
  Process only the specified feed instead of running all configured feeds. Useful for testing or manual processing of individual feeds.

- `--no-download`  
  Skip downloading new episodes and only process existing files to generate RSS feeds. Useful for regenerating feeds after configuration changes.

### Media Options
- `--refresh-thumbnails`  
  Force refresh of feed thumbnails even if they already exist.

- `--ratelimit RATE`  
  Set download rate limit (e.g., `500K`, `1M`, `2MB`). Supports both bytes (kB, MB) and bits (kb, Mb) per second. Overrides any rate limit specified in the config file.

- `--ignore-ratelimit`  
  Ignore any rate limit specified in the config file and download at maximum speed.

### Logging and Debug
- `--log LOG_FILE`  
  Specify log file location (default: `/var/log/scrape23.log`).

- `--debug`  
  Enable debug logging for more verbose output.

### Examples

Initialize environment:
```bash
scrape23 --initialize --config myfeeds.toml
```

Set up archives without downloading past episodes:
```bash
scrape23 --initialize-archives --config myfeeds.toml
```

Process a single feed with rate limiting:
```bash
scrape23 --feed myfeed --ratelimit 1MB --config myfeeds.toml
```

Regenerate RSS without downloading:
```bash
scrape23 --no-download --refresh-thumbnails --config myfeeds.toml
```

Run with debug logging:
```bash
scrape23 --debug --log /tmp/scrape23-debug.log --config myfeeds.toml
```

### Service Mode

When run without the `--feed` option, scrape23 operates in service mode, continuously monitoring all configured feeds according to their individual schedules defined in the configuration file.