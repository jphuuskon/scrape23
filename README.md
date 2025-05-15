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
5. check `scrape23.toml.sample` file for configuration example

6. Initialize the environment and archives with:
    ```bash
    scrape23 --initialize
    scrape23 --initialize-archives --config yourconfigfile.toml
    ```

7. Add scrape23 to your crontab. This example runs scrape23 five minutes past the hour every three hours:
    ```
    5 */3 * * *  scrape23 --config yourconfigfile.toml
    ```

8. Subscribe to your feeds on your podcast client.

