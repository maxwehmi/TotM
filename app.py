import os
import config
import TotM_top as top
import TotM_auxillary as aux
import spotipy
import logging
import time
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from spotipy.oauth2 import SpotifyOAuth
from threading import Thread

# app setup
TIME_DELTA = 7200 # 2h*60min/h*60s/min
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.INFO, filename='TotM-App.log', filemode='a')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#app.config['SERVER_NAME'] = 'totm.berlin'
app.secret_key = config.secret_Key
db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()


def create_spotify_oauth(cache):
    """Creates a new SpotifyOAuth object with the required scope and cache as the cache path"""

    return SpotifyOAuth(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=url_for('redirect', _external=True),
            scope="playlist-modify-private,user-top-read,user-read-recently-played",
            cache_path=cache)


class User(db.Model):
    """To save the users which are subscribed to TotM"""

    userid = db.Column(db.String(30), unique=True, primary_key=True)
    token = db.Column(db.String(300), nullable=False)
    refresh_token = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return '<User: %r>' % self.userid


@app.route('/') 
def index():
    sp_oauth_global = create_spotify_oauth(config.global_cache)
    auth_url = sp_oauth_global.get_authorize_url()
    return render_template('index.html', link=auth_url)


@app.route('/imprint')
def imprint():
    return render_template('imprint.html')


@app.route('/redirect')
def redirect():
    # If the user approved, the access code will be contained in the URL
    code = request.args.get('code')

    if not code:
        app.logger.warning('No code found in URL.')
        return render_template('redirect.html', call="ERROR")
    
    app.logger.info('Code found in URL, trying to process it...')

    # Tries to generate the token info from the acces code
    sp_oauth = create_spotify_oauth(config.tmp_cache)

    try:
        sp_oauth.get_access_token(code, as_dict=False)
    except:
        app.logger.error('Could not process code.')
        return render_template('redirect.html', call="ERROR")

    token_info = sp_oauth.get_cached_token()
    if os.path.isfile(config.tmp_cache):
        os.remove(config.tmp_cache)

    try: 
        sp = spotipy.Spotify(token_info['access_token'])
        user_id = sp.current_user()['id']
    except: 
        app.logger.error('Could not retreive token_info. User is probably not registered as a tester.')
        return render_template('redirect.html', call="ERROR")

    user = db.session.get(User,user_id) 

    app.logger.info('Got the token for ' + user_id + '. Checking if user is already in the database...')

    if user:
        app.logger.info('User already in database.')
        return render_template('redirect.html', call="ALREADY_IN_DB")

    app.logger.info('User not in database. Trying to add user...')

    new_user = User(
        userid=user_id,
        token=token_info['access_token'],
        refresh_token=token_info['refresh_token'],
        timestamp=time.time())

    try:
        db.session.add(new_user)
        db.session.commit()
        app.logger.info('Successfully added new user to database.')
        return render_template('redirect.html', call="SUCC")
    except:
        app.logger.warning('There was an error adding the user to the database.')
        return render_template('redirect.html', call="ERROR")
    


@app.route('/unsub', methods=['POST','GET'])
def unsub():
    if request.method == 'POST':
        # If the user clicks the unsubscribe button, he invokes the POST method
        userid = request.form['content']
        user = db.session.get(User,userid) 

        app.logger.info('Trying to unsubscribe ' + userid + '.')

        if not user:
            app.logger.warning('User not found in database.')
            return render_template('unsub.html',call="USER_NOT_FOUND")
        
        app.logger.info('User found in database. Trying to remove user...')

        try:
            db.session.delete(user)
            db.session.commit()
            app.logger.info('Successfully removed user from databse.')
            app.logger.info('Trying to remove their file...')
            if os.path.isfile("instance/"+userid):
                os.remove("instance/"+userid)
            app.logger.info('Successfully removed their file.')
            return render_template('unsub.html',call="SUCC")
        except:
            app.logger.info('There was an error removing the user from the database.')
            return render_template('unsub.html',call="ERROR")
    else:
        return render_template('unsub.html')


def check_Thread():
    """Controls the thread, which checks for new songs and creates the playlists."""
    app.logger.info('Started check thread')

    # sleep until the end of this month at 11 p.m.
    year = datetime.now(tz=timezone.utc).date().year
    month = datetime.now(tz=timezone.utc).date().month
    sleepSeconds = aux.calculate_sleepTime(month, year)
    app.logger.info('Sleeping for ' + str(sleepSeconds) + 's.')
    time.sleep(sleepSeconds)

    while True:
        year = datetime.now(tz=timezone.utc).date().year
        month = datetime.now(tz=timezone.utc).date().month

        with app.app_context():
            app.logger.info('End of month reached. Creating next playlist.')
            users = User.query.order_by(User.userid).all()
            for user in users:
                user_id = user.userid
                app.logger.info('Current user: ' + user_id)
                sp_oauth = create_spotify_oauth(config.tmp_cache)

                app.logger.info('Trying to refresh token...')
                try:
                    token_info = sp_oauth.refresh_access_token(user.refresh_token)
                    user.token=token_info['access_token']
                    user.refresh_token=token_info['refresh_token']
                    db.session.commit()
                    app.logger.info('Successfully got new token.')
                except:
                    app.logger.error('Could not retreive new token.')
                
                try:
                    app.logger.info('Generating playlist for user ' + user_id)
                    sp = spotipy.Spotify(user.token)
                    top.create_TotM_top(sp,year,month)
                    app.logger.info('Successfully created playlist.')
                except:
                    app.logger.error('Something went wrong while creating the playlist.')

                # remove the cache file
                if os.path.isfile(config.tmp_cache):
                    os.remove(config.tmp_cache)

                app.logger.info('Done with ' + user_id)
        
        app.logger.info('Done with this check.')

        # sleep until the end of the next month at 11 p.m.
        next_month = (month % 12) + 1
        new_year = year + int(month / 12) # If the current month is 12, i.e. the last month of the year, the year has to be increased by one
        sleepSeconds = aux.calculate_sleepTime(next_month, new_year)
        app.logger.info('Sleeping for ' + str(sleepSeconds) + 's.')
        time.sleep(sleepSeconds)


if __name__ == "__main__":
    thread = Thread(target = check_Thread)
    thread.start()
    
    app.run(debug=True, port=4000, host='127.0.0.1') # debug must be False for Timer to work properly

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)