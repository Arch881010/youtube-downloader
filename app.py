
#import the package
from pytube import YouTube
from flask import *
import flask
import os

from markupsafe import escape

app = Flask(__name__)

@app.route('/fnames')
def fname124():
    x = os.getcwd()
    #print(os.listdir('./downloads'))
    files = os.listdir("./downloads") #if os.path.isfile(f)]
    return files

@app.route('/download/')
async def dl2354():
    param = request.args.get('url')
    print(f"Downloading Video.. {param}")
    my_video = YouTube(param)
    my_video = my_video.streams.get_highest_resolution()
    print("Found best resolution, downloading.")
    my_video.download("./downloads")
    return f'{param} downloaded!'




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