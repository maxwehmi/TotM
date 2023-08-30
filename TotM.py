import calendar

def get_tracks(sp):
    """Requests the top 20 tracks of the last month for the user, to which the sp object belongs.
    Returns the json-data including those tracks."""
    response = sp.current_user_top_tracks(limit=20,offset=0,time_range='short_term')
    return response


def extract_uris_from_top(json_file):
    """Extracts the Song URIs from the passed json file. Expects the format to be the one as specified on the Spotify documentation.
    Returns a list containing the URIs."""
    uris = []
    for track in json_file['items']:
        uris.append(track['uri'])
    return uris


def create_playlist(sp, year, month_num):
    """Creats the TotM playlist for the user, to which the sp object belongs for month specified by year and month_num.
    Returns the playlist_id for further handling."""
    year_short = year % 100
    month_short = calendar.month_abbr[month_num]

    user_id = sp.current_user()['id']
    name = "TotM - " + month_short + " " + str(year_short)
    json_resp = sp.user_playlist_create(user_id, name, public=False, collaborative=False)
    playlist_id = json_resp['id']
    return playlist_id

def add_description(sp, playlist_id, year, month_num):
    """Adds the description to the given playlist."""
    month = calendar.month_name[month_num]
    user_id = sp.current_user()['id']
    description='These are your 20 Top of the Month tracks for ' + month + ' ' + str(year) + '!'
    sp.user_playlist_change_details(user_id, playlist_id, description=description)


def add_tracks(sp, playlist_id, tracks):
    """Adds the tracks to the specified playlist."""
    user_id = sp.current_user()['id']
    sp.user_playlist_add_tracks(user_id, playlist_id, tracks, position=None)


def create_TotM(sp, year, month_num):
    """Creats the TotM playlist for the user, to which the sp object belongs and the month specified by year and month_num."""
    resp = get_tracks(sp)
    uris = extract_uris_from_top(resp)
    playlist_id = create_playlist(sp, year, month_num)
    add_description(sp, playlist_id, year, month_num)
    add_tracks(sp, playlist_id, uris)


def get_latest_tracks(sp, timeStamp):
    resp = sp.current_user_recently_played(after=int(timeStamp*1000))
    return resp


def extract_uris_from_recent(json_file):
    uris = []
    for track in json_file['items']:
        uris.append(track['track']['uri'])
    return uris


def save_tracks(filename, tracks):
    file = open("instance/"+filename, "a")
    for track in tracks:
        file.write(track + "\n")
    file.close()


def new_tracks_recent(sp, timeStamp):
    resp = get_latest_tracks(sp,timeStamp)
    uris = extract_uris_from_recent(resp) 
    user_id = sp.current_user()['id']
    save_tracks(user_id,uris)


def read_tracks(filename):
    tracks = []
    with open("instance/"+filename) as file:
        while line := file.readline():
            tracks.append(line.rstrip())
    return tracks


def rank(list):
    counted = []
    count = []
    for item in list:
        if item in counted:
            index = counted.index(item)
            count[index] += 1
        else:
            counted.append(item)
            count.append(1)
    count, counted = zip(*sorted(zip(count, counted)))
    ranked_list = []
    for item in counted:
        ranked_list.append(item)
    return ranked_list


def create_TotM_recent(sp, year, month_num):
    user_id = sp.current_user()['id']
    playlist_id = create_playlist(sp, year, month_num)
    add_description(sp, playlist_id, year, month_num)
    tracks = read_tracks(user_id)
    if len(tracks) > 0:
        ranked_tracks = rank(tracks)
        ranked_tracks.reverse()
        if len(ranked_tracks) > 20:
            ranked_tracks = ranked_tracks[0:20]
        add_tracks(sp, playlist_id, ranked_tracks)