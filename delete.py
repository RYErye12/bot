import os
import datetime
import asyncio
from TikTokApi import TikTokApi
import requests

# Path to your server URL
SERVER_URL = 'http://your-server.com/receive_video_link/'

# Function to send the video link to your server
def send_video_link_to_server(video_url):
    payload = {'video_url': video_url}
    response = requests.post(SERVER_URL, data=payload)
    return response.status_code

async def check_and_send_video(tiktok_username):
    async with TikTokApi() as api:
        # Get user profile
        user = await api.user(username=tiktok_username)
        
        # Fetch the user's videos
        user_feed = user.videos(count=5)  # You can adjust the count if needed
        
        # Check if the first video was posted today
        for video in user_feed:
            video_timestamp = video.timestamp
            video_date = datetime.datetime.utcfromtimestamp(video_timestamp).date()
            today = datetime.datetime.utcnow().date()

            if video_date == today:
                video_url = f"https://www.tiktok.com/@{tiktok_username}/video/{video.id}"
                print(f"Video posted today! Sending link to server: {video_url}")
                status_code = send_video_link_to_server(video_url)
                if status_code == 200:
                    print('Video link sent successfully!')
                else:
                    print(f"Failed to send video link to server. Status code: {status_code}")
                break
        else:
            print("No videos posted today.")

# Example Usage:
tiktok_username = 'bananagrape3'  # Replace with the TikTok username you want to check
asyncio.run(check_and_send_video(tiktok_username))
