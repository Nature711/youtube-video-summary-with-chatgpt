import sqlite3
import os
from src.video_fetcher import fetch_latest_videos

VIDEOS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'videos.db'))

def generate_reports():

    fetch_latest_videos()

    # Connect to videos.db
    videos_conn = sqlite3.connect(VIDEOS_DB_PATH)
    videos_curs = videos_conn.cursor()

    # Fetch the most recent 50 videos from videos.db
    query = 'SELECT video_id, posted_timestamp, title, views, likes, caption_url, summary FROM videos ORDER BY posted_timestamp DESC LIMIT 30'
    videos_curs.execute(query)
    video_rows = videos_curs.fetchall()

    # Generate a list of reports for each video
    reports = []
    for video_row in video_rows:
        # Get the video_id and summary_id
        video_id = video_row[0]

        # Create the report dictionary
        report = {
            'title': video_row[1],
            'summary': video_row[6],
            'stats': {
                'views': video_row[3],
                'likes': video_row[4]
            },
            'transcript_link': video_row[5],
            'video_link': f'https://www.youtube.com/watch?v={video_id}'
        }
        reports.append(report)

    # Close connections and return reports
    videos_conn.close()
    return reports
