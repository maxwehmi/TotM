import spotipy
import calendar

def get_tracks(sp):
    response = sp.current_user_top_tracks(limit=20,offset=0,time_range='short_term')
    return response


def extract_uris(json_file):
    uris = []
    for track in json_file['items']:
        uris.append(track['uri'])
    return uris


def create_playlist(sp, name, description):
    user = sp.current_user()
    user_name = user['display_name']
    json_resp = sp.user_playlist_create(user_name, name, public=True, collaborative=False, description=description)
    playlist_id = json_resp['id']
    return playlist_id


def add_tracks(sp, playlist_id, tracks):
    user = sp.current_user()
    user_name = user['display_name']
    sp.user_playlist_add_tracks(user_name, playlist_id, tracks, position=None)


def create_TotM(sp, name, description):
    resp = get_tracks(sp)
    uris = extract_uris(resp)
    playlist_id = create_playlist(sp, name, description)
    add_tracks(sp, playlist_id, uris)


def create_all(users,year,month_num):
    year_short = year % 100
    month = calendar.month_name[month_num]
    month_short = calendar.month_abbr[month_num]

    description = "These are your 20 Top of the Month tracks for " + month + " " + str(year) + "!"
    
    for user in users:
        print("generating: " + user.username)
        try:
            sp = spotipy.Spotify(user.token)
            create_TotM(sp, "TotM - " + month_short + " " + str(year_short), description)
        except:
            print("ERROR")