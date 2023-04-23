# TotM 

TotM or "Top of the Month" (Pronounced: "Totem") is a service for Spotify which generates you a playlist with your top 20 songs of the past month. You can subcribe to it and will automatically receive the playlist at the end of the month. The WebApp can be found under: [totm.berlin](https://totm.berlin).

Alternatively, you can let this App run on your own server. Unless you change how the database works, you will still have to use the log in function. 

### Dependencies

Firstly, you will have to install all necessary packages. Since all of them are saved in the `requirements.txt`, you only have to run the following command:

    pip3 install -r requirements.txt

### Configuration

Secondly, you will want to configure the Spotify API. For this, you have to create a `config.py`, which contains your `client_id` and `client_secret`, which are given to you by Spotify.

In the same file I also specified a `secret_Key`, `SERVER_NAME`, `global_cache` and `tmp_cache`. Especially the last two could be hardcoded, but I added them in the `config.py` for better handling. `secret_Key` and `SERVER_NAME` are needed by Flask. The secret key is for encrypting Flask and should be a random string of characters and symbols. The server name is needed by Flask to be able to create new files, like the temporary cache. But it is only necessary, if you plan on deploying this project.

Next, you have to set up the database. For this, start a python interface on your server with the command `python` or `python3`. Then you have to enter the following commands:

    from app import app, db
    app.app_context().push()
    db.create_all()

Then the database should have been created (it is located in a folder called `instance`) and be working. You can additionally install [sqlite3](https://docs.python.org/3/library/sqlite3.html) to access its contents. After starting an interface with `sqlite3`, you can enter SQL requests.

### Run

At this point, you could just run the application with `python app.py`. But if you want to deploy it and make it available on the internet, you have to serve it with gunicorn and configure a proxy like nginx or caddy. For this, I recommend [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04).