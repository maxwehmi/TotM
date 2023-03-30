import spotipy
import calendar
import time

def get_tracks(sp):
    response = sp.current_user_top_tracks(limit=20,offset=0,time_range='short_term')
    return response


def extract_uris(json_file):
    uris = []
    for track in json_file['items']:
        uris.append(track['uri'])
    return uris


def create_playlist(sp, year, month_num):
    year_short = year % 100
    month = calendar.month_name[month_num]
    month_short = calendar.month_abbr[month_num]

    user = sp.current_user()
    user_name = user['display_name']
    name = "TotM - " + month_short + " " + str(year_short)
    description = "These are your 20 Top of the Month tracks for " + month + " " + str(year) + "!"
    json_resp = sp.user_playlist_create(user_name, name, public=True, collaborative=False, description=description)
    playlist_id = json_resp['id']
    return playlist_id


def add_tracks(sp, playlist_id, tracks):
    user = sp.current_user()
    user_name = user['display_name']
    sp.user_playlist_add_tracks(user_name, playlist_id, tracks, position=None)


def create_TotM(sp, year, month_num):
    resp = get_tracks(sp)
    uris = extract_uris(resp)
    playlist_id = create_playlist(sp, year, month_num)
    add_tracks(sp, playlist_id, uris)


def create_all(users,year,month_num,db,sp_oauth):
    for user in users:
        print("generating: " + user.username)

        now = int(time.time())
        expired = user.token_expiresAt - now < 60
        if expired:
            try:
                token_info = sp_oauth.refresh_access_token(user.refresh_token)

                user.token=token_info['access_token']
                user.token_expiresAt=token_info['expires_at']
                user.refresh_token=token_info['refresh_token']

                db.session.commit()
            except:
                print("ERROR")

        try:
            sp = spotipy.Spotify(user.token)
            create_TotM(sp, year, month_num)
        except:
            print("ERROR")