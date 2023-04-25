import os
import time
import sqlite3
from src.crawler import start_crawler
from src.summarizer import generate_summary
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi

# Constants
MAX_RESULTS = 5  # Maximum number of videos to fetch per channel
CHANNELS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'channels.db'))
VIDEOS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'videos.db'))
DRIVER_PATH = r'C:\Users\Nature\Downloads\chromedriver_win32\chromedriver.exe'

def fetch_latest_videos():

    start_crawler()

    """
    Fetches all videos published within the last 24 hours by the channels in the channels.db file and stores them in
    the videos.db file.
    """
    channels_conn = sqlite3.connect(CHANNELS_DB_PATH)
    videos_conn = sqlite3.connect(VIDEOS_DB_PATH)
    channel_curs = channels_conn.cursor()
    video_curs= videos_conn.cursor()

    # Fetch the channels from the channels database
    channel_curs.execute('SELECT channel_id FROM channels')

    # Start the driver
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    wait = WebDriverWait(driver, 10)

    # Fetch the latest videos for each channel and store them in the videos database
    for row in channel_curs.fetchall():
        channel_id = row[0]
        print(f"Processing videos for channel {channel_id}")
        # Go to the YouTube page for the channel
        url = f'https://www.youtube.com/channel/{channel_id}/videos'
        driver.get(url)

        # Get all the video elements
        video_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ytd-rich-grid-renderer ytd-rich-item-renderer")))[:MAX_RESULTS]
        print(f'Number of videos found: {len(video_elements)}')

        videos_info = []
        for video_element in video_elements:
            # Get the video published timestamp
            delta_str = video_element.find_element(By.ID, "metadata-line").text.split('•')[0].strip().split('\n')[1]
            print(f'{delta_str}')
            if 'ago' in delta_str:
                # Extract time delta from timestamp string
                if 'hour' in delta_str:
                    delta = timedelta(hours=int(delta_str.split()[0]))
                elif 'minute' in delta_str:
                    delta = timedelta(minutes=int(delta_str.split()[0]))
                else: continue # Ignore videos that are older than 24 hours

                # Get the timestamp of the video
                posted_timestamp = datetime.now() - delta
                # Extract the video ID
                video_id = video_element.find_element(By.ID, "thumbnail").get_attribute('href').split('=')[-1]
                print(f'Video id: {video_id}')
                # Get the video title
                title = video_element.find_element(By.ID, "video-title").text
                print(f'Video title: {title}')
                videos_info.append((video_id, posted_timestamp, title))

        videos = []
        for video_info in videos_info:
            video_id, posted_timestamp, title = video_info
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            driver.get(video_url)

            # Wait for the views and likes elements to be present
            views_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="info"]/span[1]')))
            likes_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="segmented-like-button"]/ytd-toggle-button-renderer/yt-button-shape/button/div[2]/span')))
            
            # Extract the views and likes information
            views = views_element.text.split(' ')[0]
            likes = likes_element.text
            print(f'Views: {views}')
            print(f'Likes: {likes}')

            transcript_url = None
            transcript_text = None
            summary = None
            try: 
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                transcript_text = ''
                for item in transcript_data:
                    transcript_text += item['text'] + ' '
                print(f'Length of transcript: {len(transcript_text)} words')
            except TranscriptsDisabled:
                # Handle the case when transcripts are disabled for the video
                print(f"Transcripts are disabled for the video with ID {video_id}")

            # Generate the summary for transcript
            summary = generate_summary(transcript_text)
            print(f'Length of summary: {len(summary)} words')
            
            videos.append((video_id, posted_timestamp, title, views, likes, summary))

        video_curs.executemany('INSERT OR IGNORE INTO videos VALUES (?, ?, ?, ?, ?, ?)', videos)
        videos_conn.commit()

        print(f'#### number of videos add: {len(videos)}')

    videos_conn.close()
    driver.quit()