
#import the package
from pytube import YouTube
from flask import Flask
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
import os

from markupsafe import escape

app = Flask(__name__)

@app.route('/fnames')
@cross_origin()
def fname124():
    x = os.getcwd()
    #print(os.listdir('./downloads'))
    files = os.listdir("./downloads") #if os.path.isfile(f)]
    return {'vids':files}

@app.route('/download/')
@cross_origin()
async def dl2354():
    param = request.args.get('url')
    print(f"Downloading Video.. {param}")
    my_video = YouTube(param)
    my_video = my_video.streams.get_highest_resolution()
    print("Found best resolution, downloading.")
    my_video.download("./downloads")
    return f'{param} downloaded!'


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


#print("Enter your URL")
#url = input("")
#my_video = YouTube(url)

#print("*********************Video Title************************")
#get Video Title
#print(my_video.title)

#print("********************Tumbnail Image***********************")
#get Thumbnail Image
#print(my_video.thumbnail_url)

#print("********************Download video*************************")
#get all the stream resolution for the 
#for stream in my_video.streams:
    #print(stream)

#set stream resolution
#my_video = my_video.streams.get_highest_resolution()

#or
#my_video = my_video.streams.first()

#Download video
#my_video.download("./downloads")