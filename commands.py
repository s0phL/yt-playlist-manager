import playlist_cache
import utils
import globals
import re

# Gets a playlist to edit
def select_playlist(youtube):
    pl_link_pattern = re.compile(r'(youtu\.be/|list=)([^#&?]+)') # regex from here: https://stackoverflow.com/questions/5288941/validating-youtube-playlist-url-using-regex
    
    while True:
        pl_link = input("Enter playlist link: ")

        match = pl_link_pattern.search(pl_link)

        if match:
            playlist_id = match.group(2)
            break
        else:
            print("⚠ Please input a valid link.")

    try:
        channel_id = utils.get_channel_id(youtube)
        playlist_channel_id = utils.get_playlist_channel_id(youtube, playlist_id)

        if channel_id != playlist_channel_id:
            raise PermissionError("Channel mismatch")

    except PermissionError:
        print("⚠ You do NOT own this playlist.")
        return ""

    print(f"You are now editing playlist <{playlist_id}>")
    globals.CURR_PLAYLIST_TITLE = utils.get_playlist_title(youtube, playlist_id)

    print("Caching playlist items...")
    items = utils.get_playlist_items(youtube, playlist_id)
    globals.PLAYLIST_CACHE = playlist_cache.PlaylistCache(playlist_id=playlist_id, items=items)
    print(f"Cached {len(items)} playlist items")
    
    return playlist_id

# Inserts a video into playlist
def insert_video(youtube, playlist_id):

    if playlist_id == "":
        print("⚠ Please select a playlist first.")
        return

    cache = globals.PLAYLIST_CACHE
    playlist_length = cache.length()
    print(f"*acquired playlist length: {playlist_length}*")

    # --------- User Input ---------

    vid_link_pattern = re.compile(r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|shorts\/|v\/)?)([\w\-]{11})((?:\?|\&)\S+)?$') # regex from: https://stackoverflow.com/questions/19377262/regex-for-youtube-url

    while True: 
        vid_link = input("Enter video link here: ")
        match = vid_link_pattern.search(vid_link)
        if match:
            vid_id = match.group(6)  
            break
        else:
            print("⚠ Please input a valid link.")

    #print(f"vid id: {vid_id}")

    while True:
        target_pos = input("Enter the video's desired position in playlist: ")
        try:
            target_pos = int(target_pos)
            break
        except ValueError: 
            print("⚠ Please enter a number for the position.")

    target_pos-=1 # playlist indexes start at 0

    target_pos = utils.clamp_position(target_pos, playlist_length)
    print("*clamped position*")

    # --------- Playlist Editing ---------

    # Check if video already exists
    if cache.contains(vid_id):
        item = cache.get_item(vid_id)
        playlist_item_id = item["id"]
        current_pos = item["snippet"]["position"]
        print(f"⚠ Video already in playlist at position {current_pos+1}. Moving to {target_pos+1}...")
        
        # Check if playlist is small enough to update directly
        if (playlist_length <= 50):
            item = utils.update_item(youtube, playlist_item_id, playlist_id, vid_id, target_pos)
        else:
            item = utils.move_item_binary(youtube, playlist_id, playlist_item_id, vid_id, current_pos, target_pos)

        # Update cache
        cache.update(item)
    
    else:
        print("Video not in playlist. Inserting...")
        
        # Check if playlist is small enough to insert directly
        if (playlist_length <= 50):
            item = utils.insert_item(youtube, playlist_id, vid_id, target_pos)
            playlist_item_id = item["id"]
        else:
            playlist_item_id = utils.insert_item(youtube, playlist_id, vid_id, playlist_length-1)["id"]
            print("finished end insert")
            current_pos = playlist_length
            item = utils.move_item_binary(youtube, playlist_id, playlist_item_id, vid_id, current_pos, target_pos)
            playlist_length+=1

        # Update cache
        cache.insert(item)

    yt_link = f"https://youtu.be/{vid_id}"
    pl_link = f"https://www.youtube.com/playlist?list={playlist_id}"

    print(f"✔︎ Inserted {yt_link} at position {target_pos+1} in playlist {pl_link}")

# Find video in playlist
def find_video():
    cache = globals.PLAYLIST_CACHE
    if cache is None:
        print("⚠ Please select a playlist first.")
        return
    
    title = input("Enter video title: ")

    for item in cache.video_index.values():
        vid_title = item["snippet"].get("title", "")
        if title.lower() in vid_title.lower():
            vid_id = item["snippet"]["resourceId"]["videoId"]
            position = item["snippet"].get("position")

            print("Video Found!")
            print(f"[{position+1}] https://youtu.be/{vid_id} {vid_title}")
            return
    print("⚠ Video not found")

# Delete video from playlist
def delete_video(youtube, playlist_id):
    cache = globals.PLAYLIST_CACHE
    if cache is None:
        print("⚠ Please select a playlist first.")
        return

    vid_link_pattern = re.compile(r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|shorts\/|v\/)?)([\w\-]{11})((?:\?|\&)\S+)?$') # regex from: https://stackoverflow.com/questions/19377262/regex-for-youtube-url
    vid_found = False

    video = input("Enter video title or YouTube link: ")

    match = vid_link_pattern.search(video)
    if match:
        # Entered link
        vid_id = match.group(6)  
        if cache.contains(vid_id):
            item = cache.get_item(vid_id)
            playlist_item_id = item["id"]
            vid_found = True
    else:
        # Entered title
        for item in cache.video_index.values():
            vid_title = item["snippet"].get("title", "")
            if video.lower() in vid_title.lower():
                playlist_item_id = item["id"]
                vid_id = item["snippet"]["resourceId"]["videoId"]
                vid_found = True
        
    if vid_found:
        utils.delete_item(youtube, playlist_item_id)
        cache.remove(vid_id)

        yt_link = f"https://youtu.be/{vid_id}"
        pl_link = f"https://www.youtube.com/playlist?list={playlist_id}"

        print(f"✔ Deleted {yt_link} from playlist {pl_link}")
    else: 
        print("⚠ Video not found.")
            
    



