import calendar

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
    month_short = calendar.month_abbr[month_num]

    user = sp.current_user()
    user_name = user['id']
    name = "TotM - " + month_short + " " + str(year_short)
    json_resp = sp.user_playlist_create(user_name, name, public=False, collaborative=False)
    playlist_id = json_resp['id']
    return playlist_id

def add_description(sp, playlist_id, year, month_num):
    month = calendar.month_name[month_num]
    user = sp.current_user()
    user_name = user['id']
    description='These are your 20 Top of the Month tracks for ' + month + ' ' + str(year) + '!'
    sp.user_playlist_change_details(user_name, playlist_id, name=None, public=None, collaborative=None, description=description)


def add_tracks(sp, playlist_id, tracks):
    user = sp.current_user()
    user_name = user['display_name']
    sp.user_playlist_add_tracks(user_name, playlist_id, tracks, position=None)


def create_TotM(sp, year, month_num):
    resp = get_tracks(sp)
    uris = extract_uris(resp)
    playlist_id = create_playlist(sp, year, month_num)
    add_description(sp, playlist_id, year, month_num)
    add_tracks(sp, playlist_id, uris)