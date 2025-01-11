from flask import Flask
from threading import Thread
import logging

app = Flask('')
# Disable Flask logging except for errors
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    server = Thread(target=run)
    server.daemon = True  # This ensures the thread will close when the main program ends
    server.start()
