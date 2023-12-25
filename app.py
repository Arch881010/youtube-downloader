
#import the package
from pytube import YouTube
from flask import *
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
import os

from markupsafe import escape

#app = Flask(__name__)

@app.route('/fnames')
@cross_origin()
def fname124():
    x = os.getcwd()
    #print(os.listdir('./downloads'))
    files = os.listdir("./downloads") #if os.path.isfile(f)]
    return {'vids':files}

@app.route('/download/')
@cross_origin()
def dl2354():
    param = request.args.get('url') 
    print(f"Downloading Video.. {param}")
    my_video = YouTube(param)
    my_video = my_video.streams.get_highest_resolution()
    print("Found best resolution, downloading.")
    my_video.download("./downloads")
    return "Video downloaded!"
