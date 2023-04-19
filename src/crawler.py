## Task 1: A crawler that retrieves the channels related to the keyword and stores them in channels.db
# Use web crawling instead of YouTube Data API to avoid rate limiting

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sqlite3
import urllib

QUERY = 'US stocks'
MAX_NUM_OF_CHANNELS = 3
CHANNELS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'channels.db'))
DRIVER_PATH = r'C:\Users\Nature\Downloads\chromedriver_win32\chromedriver.exe'

def start_crawler():
    conn = sqlite3.connect(CHANNELS_DB_PATH)
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS channels 
                 (channel_id TEXT PRIMARY KEY, channel_title TEXT)''')
    
    # Check if table is empty
    c.execute('SELECT COUNT(*) FROM channels') 
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # Set up the Selenium driver
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    wait = WebDriverWait(driver, 10)

    # Navigate to the YouTube search page for channels related to the search query
    encoded_query = urllib.parse.quote(QUERY)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAg%253D%253D"
    driver.get(search_url)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-item-section-renderer')))

    # Get search results
    channel_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-channel-renderer")))[:MAX_NUM_OF_CHANNELS]
    print(f'Number of channels found: {len(channel_elements)}')
    channels = []
    for el in channel_elements:
        channel_id = el.get_attribute('href').split('/')[-1]
        print(f'Channel ID: {channel_id}')
        channel_title_element = driver.find_element(By.CLASS_NAME, 'ytd-channel-name')
        channel_title = channel_title_element.find_element(By.ID, 'text').text
        channel = (channel_id, channel_title)
        print(f'Channel Title: {channel_title}')
        channels.append(channel)

    # Insert channels into database
    c.executemany('INSERT OR IGNORE INTO channels VALUES (?, ?)', channels)
    conn.commit()
    conn.close()

    # Quit the driver
    driver.quit()