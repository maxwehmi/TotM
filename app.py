import config
import TotM
import spotipy
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth

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
            scope="playlist-modify-public,playlist-modify-private,user-top-read") # public necessary?


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
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')

    if not code:
        return render_template('redirect.html', call="ERROR")

    token_info = sp_oauth.get_access_token(code, as_dict=True) # find out, how to do it with as_dict=False
    sp = spotipy.Spotify(auth=token_info['access_token'])
    current_user = sp.current_user()
    user_name = current_user['display_name']
    user = User.query.get(user_name)

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
        user = User.query.get(username)
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
    

@app.route('/showAll')
def showAll():
    users = User.query.order_by(User.username).all()
    return render_template('showAll.html', users=users)


if __name__ == "__main__":
    app.run(debug=True, port=4000)