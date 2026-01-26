#requires python 3.10 or above (for match)
import utils
import globals
import commands
import sys

def default():
    return 0

def main():
    youtube = utils.authenticate()
    globals.CURR_USER = utils.get_channel_name(youtube)

    playlist_id = ""

    print("––––––––––––––––––––––––––––––––––––––––––––––––")
    print("Welcome to YouTube Playlist Manger: Video Insert") 

    while True:
        print("================================================")
        print(f"Current Playlist Selected: <{globals.CURR_PLAYLIST_TITLE}>")
        print(f"Current Account: <{globals.CURR_USER}>")
        print("[1] Select New Playlist")
        print("[2] Insert Video")
        print("[3] Find Video")
        print("[4] Delete Video")
        if globals.CURR_USER == "":
            print("[5] Log In")
        else:
            print("[5] Switch Accounts")
        print("[6] Quit")

        option = input("> ")
        match option:
            case '1':
                playlist_id = commands.select_playlist(youtube)
            case '2':
                commands.insert_video(youtube, playlist_id)
            case '3':
                commands.find_video()
            case '4':
                commands.delete_video(youtube, playlist_id)
            case '5':
                youtube = utils.reauthenticate()
                globals.CURR_USER = utils.get_channel_name(youtube)
                globals.CURR_PLAYLIST_TITLE = ""
                globals.PLAYLIST_CACHE = None
                playlist_id = ""
            case '6':
                print("_____________________")
                sys.exit()
            case _:
                print("⚠ Invalid Selection.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("_____________________")
        sys.exit(130)
