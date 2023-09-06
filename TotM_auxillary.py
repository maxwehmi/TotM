import calendar

def create_playlist(sp, year, month_num, suffix): # Remove suffix after testing
    """Creats the TotM playlist for the user, to which the sp object belongs for month specified by year and month_num.
    Returns the playlist_id for further handling."""
    year_short = year % 100
    month_short = calendar.month_abbr[month_num]

    user_id = sp.current_user()['id']
    name = "TotM - " + month_short + " " + str(year_short) + " " + suffix  # Remove suffix after testing
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


def checkEndOfMonth(month,day,hour):
    """Checks if the specified date ist the end of the month, i.e. the last day of the given month and either 11 or 12 p.m.
    Returns true, if it is the end of the month and false otherwise."""
    if not hour in [22,23]:
        return False
    
    if month in [1,3,5,7,8,10,12]:
        if not day == 31:
            return False
    elif month in [4,6,9,11]:
        if not day == 30:
            return False
    else: # then its feburary
        if not day == 28:
            return False

    return True