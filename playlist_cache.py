class PlaylistCache:
    def __init__(self, playlist_id, items):
        self.playlist_id = playlist_id

        self.items = items

        self.video_index = {
            item["snippet"]["resourceId"]["videoId"]: item 
            for item in items
        }
    
    def contains(self, video_id):
        return video_id in self.video_index
    
    def get_item(self, video_id):
        return self.video_index.get(video_id)
    
    def length(self):
        return len(self.items)
    
    # Adds vid to cache
    def insert(self, playlist_item):
        vid_id = playlist_item["snippet"]["resourceId"]["videoId"]
        self.video_index[vid_id] = playlist_item
        self.items.append(playlist_item)

    # Updates vid data in cache
    def update(self, playlist_item):
        vid_id = playlist_item["snippet"]["resourceId"]["videoId"]
        self.video_index[vid_id] = playlist_item

    # Removes vid from cache
    def remove(self, video_id):
        if video_id in self.video_index:
            del self.video_index[video_id]