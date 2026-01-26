import os
import sys
import pickle
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request  #google's request
from googleapiclient.discovery import build

# Authentication

def authenticate():
    credentials = None

    # token.pickle stores the user's credentials from prev successful logins
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # if there are no valid credentials avaliable, then either refresh the token or log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Access Token...")
            credentials.refresh(Request())
        else:
            print("Fetching New Tokens...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", scopes=["https://www.googleapis.com/auth/youtube"]
                )

            # run local web server
            flow.run_local_server(port=8080, prompt="consent", authorization_prompt_message="")

            credentials = flow.credentials

            # save credentials for next run
            with open("token.pickle", "wb") as f:
                print("Saving Credentials for Future Use")
                pickle.dump(credentials, f)

    return build('youtube', 'v3', credentials=credentials)

def get_channel_id(youtube):
    request = youtube.channels().list(
        part="id",
        mine=True
    )
    response = request.execute()

    if not response["items"]:
        raise RuntimeError("No YouTube channel found for this account")

    return response["items"][0]["id"]

def get_playlist_channel_id(youtube, playlist_id):
    request = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    )
    response = request.execute()

    if not response["items"]:
        raise RuntimeError("Playlist not found or inaccessible")

    return response["items"][0]["snippet"]["channelId"]

def reauthenticate():
    os.remove("token.pickle")
    return authenticate()

# Playlist Management

def clamp_position(position, length):
    if position < 0:
        return 0
    if position > length:
        return length
    return position

def get_playlist_items(youtube, playlist_id):
    items = []
    request = youtube.playlistItems().list(
        part="id,snippet",
        playlistId=playlist_id,
        maxResults=50
    )

    while request:
        response = request.execute()
        items.extend(response["items"])
        request = youtube.playlistItems().list_next(request, response)

    return items

def insert_at_end(youtube, playlist_id, vid_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": vid_id
                }
            }
        }
    )
    response = request.execute()
    return response["id"]  # playlist item id

# Move item to target position
def move_item_binary(youtube, playlist_id, playlist_item_id, vid_id, start_pos, target_pos):
    current_pos = start_pos

    while current_pos != target_pos:
        step = (target_pos - current_pos) // 2

        if step == 0:
            new_pos = target_pos
        else:
            new_pos = current_pos + step

        request = youtube.playlistItems().update(
            part="snippet",
            body={
                "id": playlist_item_id,
                "snippet": {
                    "playlistId": playlist_id,
                    "position": new_pos,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": vid_id
                    }
                }
            }
        )
        response = request.execute()
        #print(response)
        current_pos = response["snippet"]["position"]
        print(f"moved item. current position: {current_pos}")

youtube = authenticate()

pl_link_pattern = re.compile(r'(youtu\.be/|list=)([^#&?]+)') # regex from here: https://stackoverflow.com/questions/5288941/validating-youtube-playlist-url-using-regex
vid_link_pattern = re.compile(r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|shorts\/|v\/)?)([\w\-]{11})((?:\?|\&)\S+)?$') # regex from: https://stackoverflow.com/questions/19377262/regex-for-youtube-url

print("––––––––––––––––––––––––––––––––––––––––––––––––")
print("Welcome to YouTube Playlist Manger: Video Insert")

print("================================================")
pl_link = input("Enter playlist link: ")
playlist_id = pl_link_pattern.search(pl_link)

match = pl_link_pattern.search(pl_link)

if match:
    playlist_id = match.group(2)  
else:
    print("⚠ input a valid link")
    sys.exit()

try:
    channel_id = get_channel_id(youtube)
    playlist_channel_id = get_playlist_channel_id(youtube, playlist_id)

    if channel_id != playlist_channel_id:
        raise PermissionError("Channel mismatch")

except PermissionError:
    print("⚠ Channel mismatch detected.")
    print("Re-authenticating...")

    os.remove("token.pickle")
    youtube = authenticate()

    my_channel_id = get_channel_id(youtube)
    playlist_owner_id = get_playlist_channel_id(youtube, playlist_id)

    if my_channel_id != playlist_owner_id:
        print("⚠ Playlist still not owned by this channel.")
        sys.exit()

print(f"You are now editing playlist <{playlist_id}>. Enter nothing to exit.")

items = get_playlist_items(youtube, playlist_id)
playlist_length = len(items)
print(f"*acquired playlist length: {playlist_length}*")

while True: 

    vid_link = input("Enter video link here: ")

    if vid_link == '':
        break

    match = vid_link_pattern.search(vid_link)
    if match:
        vid_id = match.group(6)  
    else:
        print("⚠ input a valid link")
        sys.exit()

    print(f"vid id: {vid_id}")

    target_pos = input("Enter the video's desired position in playlist: ")

    if target_pos == '':
        break
    target_pos = int(target_pos)

    target_pos-=1 # playlist indexes start at 0

    target_pos = clamp_position(target_pos, playlist_length)
    print("*clamped position*")

    if (playlist_length <= 50):

        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "position": target_pos,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": vid_id
                    }
                }
            }
        )

        response = request.execute()

        playlist_length+=1

    else:

        playlist_item_id = insert_at_end(youtube, playlist_id, vid_id)
        print("*finished end insert*")
        playlist_length+=1
        current_pos = playlist_length
        move_item_binary(youtube, playlist_id, playlist_item_id, vid_id, current_pos, target_pos)


    yt_link = f"https://youtu.be/{vid_id}"
    pl_link = f"https://www.youtube.com/playlist?list={playlist_id}"

    print(
        f"Inserted {yt_link} at position {target_pos+1} "
        f"in playlist {pl_link}"
    )
