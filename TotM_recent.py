import TotM_auxillary as aux

def get_tracks_recent(sp, timeStamp):
    """Requests a list of the recently played songs the user, to which the sp object belongs.
    Recently played in thits context means played after the specified timestamp.
    It returns the json-data including those tracks."""
    resp = sp.current_user_recently_played(after=int(timeStamp*1000))
    return resp


def extract_uris_from_recent(json_file):
    """Extracts the Song URIs from the passed json file. Expects the format to be the one as specified on the Spotify documentation for the recently played songs.
    Returns a list containing the URIs."""
    uris = []
    for track in json_file['items']:
        uris.append(track['track']['uri'])
    return uris


def new_tracks_recent(sp, timeStamp):
    """Gets the recently played songs from the user, to which the sp object belongs, and saves them to their file."""
    resp = get_tracks_recent(sp,timeStamp)
    uris = extract_uris_from_recent(resp) 
    user_id = sp.current_user()['id']
    save_tracks(user_id,uris)


def save_tracks(filename, tracks):
    """Saves the list of songs to the specified file"""
    file = open("instance/"+filename, "a")
    for track in tracks:
        file.write(track + "\n")
    file.close()


def read_tracks(filename):
    """Reads the lines in the specified file and returns them as a list."""
    tracks = []
    with open("instance/"+filename) as file:
        while line := file.readline():
            tracks.append(line.rstrip())
    return tracks


def rank(list):
    """Ranks the items in the list by the number of occurencies.
    Returns the ranked list, where the least common element comes first."""
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
    """Creats the TotM playlist the new way for the user, to which the sp object belongs and the month specified by year and month_num."""
    user_id = sp.current_user()['id']
    playlist_id = aux.create_playlist(sp, year, month_num, "A") # Remove suffix after testing
    aux.add_description(sp, playlist_id, year, month_num)
    tracks = read_tracks(user_id)
    if len(tracks) > 0:
        ranked_tracks = rank(tracks)
        ranked_tracks.reverse()
        if len(ranked_tracks) > 20:
            ranked_tracks = ranked_tracks[0:20]
        aux.add_tracks(sp, playlist_id, ranked_tracks)