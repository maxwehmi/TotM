# this file is executed once when the server starts. This is necessary, because otherwise the playlists would be created as many times as there are gunicorn workers
from app import check_Thread
from threading import Thread

def on_starting(server):
    thread = Thread(target = check_Thread)
    thread.start()