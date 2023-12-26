
#import the packages
from pytube import YouTube
from flask import *
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
import os

from markupsafe import escape

import sqlite3
from sqlite3 import Error

import random
import string

# get random password pf length 8 with letters, digits, and symbols
def create_key(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    print("Random password is:", password)
    return password

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

connection = create_connection("./index.db")

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
  user TEXT NOT NULL,
  password TEXT NOT NULL,
  key TEXT NOT NULL
);
"""

active_users = []
def default(data):
    ""

def execute_query(connection, query, action=default):
    cursor = connection.cursor()
    try:
        data = cursor.execute(query)
        action(data)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

execute_query(connection, create_users_table)

#app = Flask(__name__)

### Create Encryption
#import rsa 
#try: 
    #with open("private.pem", "r") as f:
    #    if(len(f.read()) > 0):
    #        ""
    #    else:
    #        Error("Missing Keys")
#except:
    #public_key, private_key = rsa.newkeys(1024)

    #with open("public.pem", "wb") as f:
    #    f.write(public_key.save_pkcs1("PEM"))

    #with open("private.pem", "wb") as f:
    #    f.write(private_key.save_pkcs1("PEM"))

@app.route('/fnames', methods=['POST'])
@cross_origin()
def fname124():
    try:
        user = request.args.get("user")
        key = request.headers.get("key")
        files = []
        if user:
            files = os.listdir(f"./downloads/{user}") #if os.path.isfile(f)]
        else:
            files = os.listdir(f"./downloads")
        return {'vids':files}
    except:
        return {'vids':"BAD_BACKEND_ERROR"}

@app.route('/download/', methods=['POST'])
@cross_origin()
def dl2354():
    try:
        param = request.args.get('url') 
        key = request.headers.get("key")
        print(f"Downloading Video.. {param}")
        my_video = YouTube(param)
        my_video = my_video.streams.get_highest_resolution()
        print("Found best resolution, downloading.")  
        my_video.download("./downloads")
        return "Video downloaded!"
    except:
        return "Failed to downlaod video. Either server is overloaded or the video is age-restricted."

@app.route('/user/create', methods=['POST'])
@cross_origin
def CrUs1241():
    user = request.headers.get("user")
    password = request.headers.get("password")
    key = create_key(50)
    # Password should already be encrypted before getting here.
    if len(password) > 50:
        ""
    else:
        return {'result':"Recieved Plain Text Password | ERR_PLAIN_PASSWORD", 'key':"SEE_RESULT"}
# Query should inclue user (txt), password (txt; encrypted), key (txt)
# Key = Auth Key
    
    query = f""" 
INSERT INTO users
(user, password, key)
VALUES
('{user}', '{password}', '{key}')
"""
    try:
        execute_query(connection, query)
        return {"result":"Sucess!", "key":key}
    except:
        return {'result':"Failed to create user.", "key":"CREATED|SEE_RESULT"}


@app.get('/user/retrive')
def findUsers():
    def store_users(data):
        active_users = data
    query = "SELECT user FROM user"
    execute_query(connection, query, store_users)
    return {'users':active_users}


