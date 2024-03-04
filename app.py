import os
import re
from pytube import YouTube
from flask import *
import flask
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import sqlite3
from sqlite3 import Error
import random
import string


#import the packages
#s.exec("pip install pytube flask flask_cors")

load_dotenv()  # take environment variables from .env.

logging.getLogger('flask_cors').level = logging.DEBUG


#from flask.ext.cors import CORS, cross_origin


app = Flask(__name__)
cors = CORS(app)#, resources={r"/*": {"origins": "*"}})

app.debug = True




# get random password pf length 8 with letters, digits, and symbols
def create_key(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

# Awful purify
def clean(string):
    try:
        regexd = ""
        if (string):
            regexd = re.sub(r"[\"\'*}<>+={$%^&!@~`?|(|),#_;[:.~(0-9)/\\\]-]", "", string)
        else:
            return ""
        if (regexd == "Undefined" or regexd == "None"):
            return ""
        return regexd
    except TypeError:
        return ""
    except Error as e:
        raise ValueError("Failed to clean string. Error: %", e)

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path, check_same_thread=False) # check_same_thread=False (https://stackoverflow.com/a/48234567)
        #print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
        raise ValueError("Failed to connect to database.")

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
        #print("Query executed successfully")
        return data
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

@app.before_request
def info():
    #print(request.url)
    #print(request.headers)
    #print(request.method)
    ""

@app.route('/fnames')
def fname124():
    req = request
    #print("")
    #print(req.method)
    try:

        # Lets not get hit with malformed requests, shall we?
        user = clean(request.args.get("user"))

        key = clean(request.headers.get("key"))

        files = []
        if user:
            files = os.listdir(f"./downloads/{user}") #if os.path.isfile(f)]
            check = execute_query(connection, "SELECT key FROM users WHERE username = '%s'", user)
            try:
                logged_key = clean(check.fetchone())
            except AttributeError:
                return flask.jsonify({'vids':["User not found?", "Clear your cookies for this website."]}) # This should NEVER happen.
            if key == logged_key:
                ""
            else: 
                return flask.jsonify({'vids':["Never Gonna Give You Up.mp4", "Your key is invalid."]})
        else:
            files = os.listdir(f"./downloads") 
        returnFiles = []
        for f in files:
            if f.endswith(".mp4"):
                returnFiles.append(f)
        response = flask.jsonify({'vids':returnFiles})
        return response
    except FileNotFoundError:
        os.mkdir(f"./downloads/{user}")
        return flask.jsonify({"vids":[]})
    except Error as e:
        print(type(e))
        response = flask.jsonify({'vids':"BAD_BACKEND_ERROR"})
        return response

@app.route('/download/')
def dl2354():
    try:
        param = request.args.get('url')
        # Lets not get hit with malformed requests, shall we?

        key = request.headers.get("key")
        key = re.sub(r"[\"\']", "", key) #Same thing. 
        print(f"Downloading Video.. {param}")
        my_video = YouTube(param)
        my_video = my_video.streams.get_highest_resolution()
        print("Found best resolution, downloading.")  
        my_video.download("./downloads")
        response = flask.jsonify({'result':"Video downloaded!"})
        return response
    except:
        response = flask.jsonify({'result': "Failed to downlaod video. Either server is overloaded or the video is age-restricted."})
        return response

@app.route('/user/create')
def CrUs1241():
    # Lets not get hit with malformed requests, shall we?
    user = clean(request.args.get("user"))
    password = clean(request.args.get("password"))

    key = create_key(50)
    # Password should already be encrypted before getting here.
    if len(password) > 50:
        ""
    else:
        response = flask.jsonify({'result':"Recieved Plain Text Password | ERR_PLAIN_PASSWORD", 'key':"SEE_RESULT"})
        return flask.jsonify({'result':"Recieved Plain Text Password | ERR_PLAIN_PASSWORD", 'key':"SEE_RESULT"})
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
        response = flask.jsonify({"result":"Sucess!", "key":key})
        return response
    except:
        response = flask.jsonify({'result':"Failed to create user.", "key":"CREATED|SEE_RESULT"})
        return response


@app.get('/user/retrive')
def findUsers():
    def store_users(data):
        active_users = data
    query = "SELECT user FROM users"
    execute_query(connection, query, store_users)
    response = flask.jsonify({'users':active_users})

    return response

@app.route("/download")
def dwn241():
    return ""

@app.errorhandler(404)
def page_not_found(e):
    return request.url

@app.after_request
def after_request(response):
    if (request.headers.get(['X-Forward-Host'])):
        response.headers.add('Access-Control-Allow-Origin', request.headers['X-Forward-Host'])
    else:
        response.headers.add('Access-Control-Allow-Origin', os.getenv('guiurl')[0:-1])
    #response.headers.add('Access-Control-Allow-Origin', os.getenv('guiurl')[0:-1])
    #print(request.url)
    #response.headers.add('Acccess-Control-Allow-Orgion', request.url)
    #print("Access-Control-Allow-Origin", os.getenv('guiurl'))
    #print(response.headers['Access-Control-Allow-Origin'])
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add("Access-Control-Expose-Headers","*")
    response.headers.add("test", "completed")
    return response

@app.get('/video/<string:url>')
def a():
    ""

if __name__ == '__main__':
    app.run()
