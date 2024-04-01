import calendar
from datetime import datetime

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
    sp.user_playlist_change_details(user_id, playlist_id, public=False, description=description)


def add_tracks(sp, playlist_id, tracks):
    """Adds the tracks to the specified playlist."""
    user_id = sp.current_user()['id']
    sp.user_playlist_add_tracks(user_id, playlist_id, tracks, position=None)


def lastDay(month):
    """Returns the date of the last day of the month."""
    if month in [1,3,5,7,8,10,12]:
        return 31
    elif month in [4,6,9,11]:
        return 30
    else: # then its feburary
        return 28


def calculate_sleepTime(month, year):
    """Calculates the time until the end of the given month in seconds."""
    now = datetime.now()
    last_day = lastDay(month)
    future = datetime(year,month,last_day,23,0)
    return (future-now).total_seconds()