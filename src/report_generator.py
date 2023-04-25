import sqlite3
import os
from datetime import datetime, timedelta
from src.video_fetcher import fetch_latest_videos

VIDEOS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'videos.db'))
MAX_NUM_OF_RESULTS = 20

def generate_reports(last_fetch_time):

    # Connect to videos.db
    videos_conn = sqlite3.connect(VIDEOS_DB_PATH)
    video_curs = videos_conn.cursor()

    # Create the videos table if it does not exist
    video_curs.execute('CREATE TABLE IF NOT EXISTS videos (video_id TEXT PRIMARY KEY, '
                    'posted_timestamp INTEGER, title TEXT, views TEXT, likes TEXT, summary TEXT)')
    video_curs.execute('CREATE INDEX IF NOT EXISTS idx_videos_posted_timestamp ON videos (posted_timestamp)')

    # Check if table is empty
    video_curs.execute('SELECT COUNT(*) FROM videos')
    is_videos_db_empty = video_curs.fetchone()[0] == 0
    is_after_one_hour = (datetime.now() - last_fetch_time) > timedelta(hours=1)

    # Check if it has been at least one hour since the last fetch and the database is not empty
    if is_after_one_hour or is_videos_db_empty:
        fetch_latest_videos()
        last_fetch_time = datetime.now()

    # Fetch the most recent 50 videos from videos.db
    query = f'SELECT video_id, posted_timestamp, title, views, likes, summary FROM videos ORDER BY posted_timestamp DESC LIMIT {MAX_NUM_OF_RESULTS}'
    video_curs.execute(query)
    video_rows = video_curs.fetchall()

    # Generate a list of reports for each video
    reports = []
    for video_row in video_rows:
        # Get the video_id and summary_id
        video_id = video_row[0]
        print(f'display report for video: {video_row[2]}')

        # Create the report dictionary
        report = {
            'title': video_row[2],
            'summary': video_row[5],
            'stats': {
                'views': video_row[3],
                'likes': video_row[4]
            },
            'transcript_link': f'https://www.youtube.com/watch?v={video_id}',
            'video_link': f'https://www.youtube.com/watch?v={video_id}'
        }
        reports.append(report)

    # Close connections and return reports
    videos_conn.close()
    return reports
