import os
import config
import TotM
import spotipy
import logging
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
from threading import Timer

# app setup
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG, filename='TotM-App.log', filemode='a')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SERVER_NAME'] = 'totm.berlin'
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
            redirect_uri=url_for('redirectPage', _external=True),
            scope="playlist-modify-private,user-top-read",
            cache_path=cache)

 
def create_all(users,year,month_num):
    """Creats TotM playlists for all user in users. year and month_num describe the year and month to which the playlist belongs"""

    app.logger.info('Start generating all TotM playlists.')
    for user in users:
        app.logger.info('Start generating playlist for ' + user.userid + '.')
        sp_oauth = create_spotify_oauth(config.tmp_cache)
        app.logger.info('Trying to refresh access token...')
        try:
            token_info = sp_oauth.refresh_access_token(user.refresh_token)

            app.logger.info('Got new access token, trying to add it to the database...')

            user.token=token_info['access_token']
            user.refresh_token=token_info['refresh_token']
            db.session.commit()

            app.logger.info('Successfully added the new token to the database.')
        except:
            app.logger.error('Something went wrong while trying to get the new access token.')

        try:
            app.logger.info('Generating playlist...')
            sp = spotipy.Spotify(user.token)
            TotM.create_TotM(sp, year, month_num)
            app.logger.info('Done!')
        except:
            app.logger.error('Something went wrong while creating the playlist')

        if os.path.isfile(config.tmp_cache):
            os.remove(config.tmp_cache)

    app.logger.info('Finished generating all TotM playlists')


class User(db.Model):
    """To save the users which are subscribed to TotM"""

    userid = db.Column(db.String(30), unique=True, primary_key=True)
    token = db.Column(db.String(300), nullable=False)
    refresh_token = db.Column(db.String(300), nullable=False)
    
    def __repr__(self):
        return '<User: %r>' % self.userid


@app.route('/') 
def index():    
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    app.logger.debug(ip + ' accessed the website.')
    sp_oauth_global = create_spotify_oauth(config.global_cache)
    auth_url = sp_oauth_global.get_authorize_url()
    return render_template('index.html', link=auth_url)


@app.route('/imprint')
def imprint():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    app.logger.debug(ip + ' accessed the imprint.')
    return render_template('imprint.html')


@app.route('/redirect')
def redirectPage():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    app.logger.debug(ip + ' accessed the redirect.')
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
        refresh_token=token_info['refresh_token'])

    try:
        db.session.add(new_user)
        db.session.commit()
        app.logger.info('Successfully added new user to database.')
        return render_template('redirect.html', call="SUCC")
    except:
        app.logger.info('There was an error adding the user to the database.')
        return render_template('redirect.html', call="ERROR")
    


@app.route('/unsub', methods=['POST','GET'])
def unsub():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    app.logger.debug(ip + ' accessed the unsub.')
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
            return render_template('unsub.html',call="SUCC")
        except:
            app.logger.info('There was an error removing the user from the database.')
            return render_template('unsub.html',call="ERROR")
    else:
        return render_template('unsub.html')
    

def generate_all():
    """Generates TotM playlists for all users for the current month.
    This is basically a handler for the create_all method."""
    with app.app_context():
        year = datetime.utcnow().date().year
        month = datetime.utcnow().date().month
        users = User.query.order_by(User.userid).all()
        create_all(users,year,month)


def timers():
    # dates are currently hardcoded, this will be solved in a future version with multiple threads
    now = datetime.now()

    end_of_april = datetime(2023, 4, 30, 23, 0, 0, 0)
    delay_april = (end_of_april - now).total_seconds()
    t = Timer(delay_april, generate_all)
    t.start()
    app.logger.info('Started timer for end of april. It will go of in ' + str(delay_april) + 's.')

    end_of_may = datetime(2023, 5, 31, 23, 0, 0, 0)
    delay_may = (end_of_may - now).total_seconds()
    t2 = Timer(delay_may, generate_all)
    t2.start()
    app.logger.info('Started timer for end of may. It will go of in ' + str(delay_may) + 's.')


if __name__ == "__main__":
    timers()
    app.run(debug=False, port=4000) # debug must be False for Timer to work properly

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)