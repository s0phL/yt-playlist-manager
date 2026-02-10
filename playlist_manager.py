import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request  #google's request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

# Authentication

def authenticate():
    credentials = None

    # token.pickle stores the user's credentials from prev successful logins
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    
    if credentials and credentials.valid:
        return build('youtube', 'v3', credentials=credentials)

    # if there are no valid credentials avaliable, then either refresh the token or log in
    try:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Access Token...")
            credentials.refresh(Request())
        else:
            raise RefreshError("No valid credentials")
    
    except RefreshError:
            print("⚠ Stored credentials are invalid")
            if os.path.exists("token.pickle"):
                os.remove("token.pickle")

            print("Fetching New Tokens...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", scopes=["https://www.googleapis.com/auth/youtube"]
            )

            # run local web server
            flow.run_local_server(port=8080, prompt="consent", authorization_prompt_message="")

            credentials = flow.credentials

            #print(credentials.to_json())

            # save credentials for next run
            with open("token.pickle", "wb") as f:
                print("Saving Credentials for Future Use")
                pickle.dump(credentials, f)

    return build('youtube', 'v3', credentials=credentials)

def reauthenticate():
    if os.path.exists("token.pickle"):
        os.remove("token.pickle")
    return authenticate()

def get_channel_info(youtube):
    request = youtube.channels().list(
        part="id,snippet",
        mine=True
    )
    response = request.execute()

    if not response["items"]:
        raise RuntimeError("⚠ No YouTube channel found for this account.")

    return response

def get_channel_id(youtube):
    response = get_channel_info(youtube)
    return response["items"][0]["id"]

def get_channel_name(youtube):
    response = get_channel_info(youtube)
    return response["items"][0]["snippet"]["title"]

def get_playlist_channel_info(youtube, playlist_id):
    request = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    )
    response = request.execute()

    if not response["items"]:
        raise RuntimeError("⚠ Playlist not found or inaccessible.")

    return response

def get_playlist_channel_id(youtube, playlist_id):
    response = get_playlist_channel_info(youtube, playlist_id)
    return response["items"][0]["snippet"]["channelId"]

def get_playlist_title(youtube, playlist_id):
    response = get_playlist_channel_info(youtube, playlist_id)
    return response["items"][0]["snippet"]["title"]

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

def insert_item(youtube, playlist_id, vid_id, target_pos):
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
    return response 

def update_item(youtube, playlist_item_id, playlist_id, vid_id, target_pos):
    request = youtube.playlistItems().update(
        part="snippet",
        body={
            "id": playlist_item_id,
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
    return response

# Move item to target position
def move_item_binary(youtube, playlist_id, playlist_item_id, vid_id, current_pos, target_pos):
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
        current_pos = response["snippet"]["position"]

        print(f"*moved item. current position: {current_pos}*")
    
    return response

def delete_item(youtube, playlist_item_id):
    request = youtube.playlistItems().delete(
        id=playlist_item_id
    )
    response = request.execute()