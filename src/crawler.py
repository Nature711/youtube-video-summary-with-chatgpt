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
MAX_NUM_OF_CHANNELS = 10
CHANNELS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'channels.db'))
DRIVER_PATH = r'C:\Users\Nature\Downloads\chromedriver_win32\chromedriver.exe'

# Set up the Selenium driver
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
wait = WebDriverWait(driver, 10)

def get_channel_id_and_title(channel_link):
    # Navigate to the YouTube channel page
    driver.get(channel_link)
    # Get the channel title
    channel_title = driver.title.split(' - YouTube')[0]
    # Simulate Ctrl+U to view page source
    body = driver.find_element(By.TAG_NAME, 'body')
    body.send_keys(Keys.CONTROL + 'u')
    # Wait for page source to load
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'html')))
    # Find the channel ID in the page source
    try:
        channel_id = driver.page_source.split('itemprop="channelId" content="')[1].split('"')[0]
    except IndexError:
        channel_id = None
    return channel_id, channel_title

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
    
    # Navigate to the YouTube search page for channels related to the search query
    encoded_query = urllib.parse.quote(QUERY)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAg%253D%253D"

    driver.get(search_url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-item-section-renderer')))
    channel_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-channel-renderer")))[:MAX_NUM_OF_CHANNELS]

    channel_links = set()
    for channel_ele in channel_elements:
        channel_link = channel_ele.get_attribute('href')
        channel_links.add(channel_link)
        print(f'found channel with link: {channel_link}')

    channels = set()
    for link in channel_links:
        channel_id, channel_title = get_channel_id_and_title(link)
        if (channel_id is None): continue
        print(f'Channel ID: {channel_id}')
        print(f'Channel Title: {channel_title}')
        channel = (channel_id, channel_title)
        channels.add(channel)

    # Insert channels into database
    c.executemany('INSERT OR IGNORE INTO channels VALUES (?, ?)', channels)
    print(f'Number of channels added: {len(channels)}')
    conn.commit()
    conn.close()

    # Quit the driver
    driver.quit()