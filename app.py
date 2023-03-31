import time
import config
import TotM
import spotipy
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
from threading import Timer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = config.secret_Key
db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()


def create_spotify_oauth():
    return SpotifyOAuth(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=url_for('redirectPage', _external=True),
            scope="playlist-modify-private,playlist-modify-public,user-top-read")


def create_all(users,year,month_num,db,sp_oauth):
    for user in users:
        print("generating: " + user.username)

        now = int(time.time())
        expired = user.token_expiresAt - now < 60
        if expired:
            try:
                # should sp = spotipy.Spotify(user.token) be used instead of sp_oauth?
                token_info = sp_oauth.refresh_access_token(user.refresh_token)

                user.token=token_info['access_token']
                user.token_expiresAt=token_info['expires_at']
                user.refresh_token=token_info['refresh_token']

                db.session.commit()
            except:
                print("ERROR: expired")

        try:
            sp = spotipy.Spotify(user.token)
            TotM.create_TotM(sp, year, month_num)
        except:
            print("ERROR: something else")



class User(db.Model):
    username = db.Column(db.String(30), unique=True, primary_key=True)
    token = db.Column(db.String(300), nullable=False)
    token_expiresAt = db.Column(db.Integer, nullable=False)
    refresh_token = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        username = '{username: %r}' % self.username
        token = '{token: %r}' % self.token
        token_expiresAt = '{token_expiresAt: %r}' % self.token_expiresAt
        refresh_token = '{refresh_token: %r}' % self.refresh_token
        data = '[' + username + ',' + token + ',' + token_expiresAt + ',' + refresh_token + ']'
        return data


@app.route('/') 
def index():    
    sp_oauth_global = create_spotify_oauth()
    auth_url = sp_oauth_global.get_authorize_url()
    return render_template('index.html', link=auth_url)


@app.route('/imprint')
def imprint():
    return render_template('imprint.html')


@app.route('/redirect')
def redirectPage():
    code = request.args.get('code')

    if not code:
        return render_template('redirect.html', call="ERROR")

    sp_oauth = create_spotify_oauth()
    sp_oauth.get_access_token(code, as_dict=False)
    token_info = sp_oauth.get_cached_token()
    print(token_info)

    sp = spotipy.Spotify(token_info['access_token'])
    current_user = sp.current_user()
    user_name = current_user['display_name']
    user = db.session.get(User,user_name) 
    print(user_name)

    if user:
        return render_template('redirect.html', call="ALREADY_IN_DB")

    new_user = User(
        username=user_name,
        token=token_info['access_token'],
        token_expiresAt=token_info['expires_at'],
        refresh_token=token_info['refresh_token'])

    try:
        db.session.add(new_user)
        db.session.commit()
        return render_template('redirect.html', call="SUCC")
    except:
        return render_template('redirect.html', call="ERROR")
    


@app.route('/unsub', methods=['POST','GET'])
def unsub():
    if request.method == 'POST':
        username = request.form['content']
        user = db.session.get(User,username) 
        if not user:
            return render_template('unsub.html',call="USER_NOT_FOUND")
        
        try:
            db.session.delete(user)
            db.session.commit()
            return render_template('unsub.html',call="SUCC")
        except:
            return render_template('unsub.html',call="ERROR")
    else:
        return render_template('unsub.html')
    

# to be removed before deployment
@app.route('/showAll')
def showAll():
    users = User.query.order_by(User.username).all()
    generate_all()
    return render_template('showAll.html', users=users)
    

def generate_all():
    with app.app_context():
        year = datetime.utcnow().date().year
        month = datetime.utcnow().date().month
        users = User.query.order_by(User.username).all()
        sp_oauth = create_spotify_oauth()
        create_all(users,year,month,db,sp_oauth)


if __name__ == "__main__":
    # dates are currently hardcoded, this will be solved in a future version with multiple threads
    """
    now = datetime.now()

    end_of_april = datetime(2023, 4, 30, 23, 0, 0, 0)
    delay_april = (end_of_april - now).total_seconds()
    print(delay_april)
    t = Timer(delay_april, generate_all)
    t.start()

    end_of_may = datetime(2023, 5, 31, 23, 0, 0, 0)
    delay_may = (end_of_may - now).total_seconds()
    print(delay_may)
    t2 = Timer(delay_may, generate_all)
    t2.start()
    """

    app.run(debug=True, port=4000) # debug must be False for Timer to work properly