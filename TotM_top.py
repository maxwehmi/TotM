import TotM_auxillary as aux

def get_tracks_top(sp):
    """Requests the top 20 tracks of the last month for the user, to which the sp object belongs.
    Returns the json-data including those tracks."""
    response = sp.current_user_top_tracks(limit=20,offset=0,time_range='short_term')
    return response


def extract_uris_from_top(json_file):
    """Extracts the Song URIs from the passed json file. Expects the format to be the one as specified on the Spotify documentation for the top songs.
    Returns a list containing the URIs."""
    uris = []
    for track in json_file['items']:
        uris.append(track['uri'])
    return uris


def create_TotM_top(sp, year, month_num):
    """Creats the TotM playlist the old way for the user, to which the sp object belongs and the month specified by year and month_num."""
    resp = get_tracks_top(sp)
    uris = extract_uris_from_top(resp)
    playlist_id = aux.create_playlist(sp, year, month_num)
    aux.add_description(sp, playlist_id, year, month_num)
    aux.add_tracks(sp, playlist_id, uris)