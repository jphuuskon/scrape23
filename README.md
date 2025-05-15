# Scrape23

Scrape23 is a utility to convert any YouTube channel into a podcast feed served from your own web server. It uses yt-dlp to download videos and extract audio to mp3 and genRSS to generate the RSS feed file. 

## Features
- Turns any Youtube URL into a podcast channel. This can be a @channel or even a search URL, though I recommend you point it to a @channel/videos URL.
- Uses yt-dlp to download videos and extract audio tracks into MP3 and mutagen to cleanup the MP3 metadata to prevent genRSS from crashing and lxml to fix the publication dates. One of these days I'll contribute an update to genRSS so that these both would become redundant.
- generates the RSS feed file with genRSS.

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

4. yt-dlp uses ffmpeg so you migh want to ensure you have `ffmpeg` installed:
    ```bash
    sudo apt install ffmpeg
    ```


