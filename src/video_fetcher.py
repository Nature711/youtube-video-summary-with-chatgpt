import datetime
import os
import time
import sqlite3
from src.crawler import start_crawler
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.summarizer import generate_summary
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

# Constants
MAX_RESULTS = 3  # Maximum number of videos to fetch per channel
MAX_AGE = 24 * 60 * 60  # Maximum age (in seconds) of videos to fetch
API_KEY = os.environ['YOUTUBE_DATA_API_KEY']
CHANNELS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'channels.db'))
VIDEOS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'videos.db'))

load_dotenv()

# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_tanscript(video_id): 
    # Call the YouTube Data API's videos.list method to retrieve the video resource
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    # Extract the video title
    video_title = video_response["items"][0]["snippet"]["title"]

    # Call the YouTube Transcript API to retrieve the transcript
    transcript_response = youtube.videos().list(
        part="id,snippet",
        id=video_id,
        captions=True
    ).execute()

    # Extract the transcript
    caption_track = transcript_response["items"][0]["snippet"]["captionTracks"][0]
    caption_url = caption_track["baseUrl"]
    caption_file = urllib.request.urlopen(caption_url)
    caption_text = caption_file.read().decode("utf-8")

    return caption_url, caption_text

def fetch_latest_videos():

    start_crawler()

    """
    Fetches all videos published within the last 24 hours by the channels in the channels.db file and stores them in
    the videos.db file.
    """
    channels_conn = sqlite3.connect(CHANNELS_DB_PATH)
    video_conn = sqlite3.connect(VIDEOS_DB_PATH)
    channel_cur = channels_conn.cursor()
    video_curs= video_conn.cursor()

    # Create the videos table if it does not exist
    video_curs.execute('CREATE TABLE IF NOT EXISTS videos (video_id TEXT PRIMARY KEY, '
                    'posted_timestamp INTEGER, title TEXT, views INTEGER, likes INTEGER, caption_url TEXT, summary TEXT)')
    video_curs.execute('CREATE INDEX IF NOT EXISTS idx_videos_posted_timestamp ON videos (posted_timestamp)')

    # Fetch the channels from the channels database
    channel_cur.execute('SELECT channel_id FROM channels')
    channel_ids = [row[0] for row in channel_cur.fetchall()]

    # Fetch the latest videos for each channel and store them in the videos database
    for channel_id in channel_ids:
        print(f'fetching data for channel with id:{channel_id}')
        try:
            # Fetch the latest videos for the channel
            channel_response = youtube.channels().list(
                part='snippet',
                forUsername=channel_id
            ).execute()
            channel_uid = channel_response['items'][0]['id']

            print(f'channel uid: {channel_uid}')

            # Retrieve video resources for the channel
            search_response = youtube.search().list(
                part='id,snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=MAX_RESULTS
            ).execute()

            # Extract the video data and insert it into the videos database
            videos = []
            for search_result in search_response.get('items', []):
                print(search_result)
                video_id = search_result['id']['videoId']
                published_at = datetime.datetime.fromisoformat(search_result['snippet']['publishedAt'][:-1])
                posted_timestamp = int(published_at.timestamp())
                age = int(time.time() - posted_timestamp)
                if age <= MAX_AGE:
                    title = search_result['snippet']['title']
                    views = 0
                    likes = 0
                    caption_url, caption_text = get_video_tanscript(video_id=video_id)
                    summary = generate_summary(caption_text)
                    videos.append((video_id, posted_timestamp, title, views, likes, caption_url, summary))

            video_curs.executemany('INSERT OR IGNORE INTO videos VALUES (?, ?, ?, ?, ?, ?, ?)', videos)
            video_conn.commit()

        except HttpError as error:
            print(f'An HTTP error {error.resp.status} occurred: {error.content}')
            continue
