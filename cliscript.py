import os
from yt_dlp import YoutubeDL
import flask as flask

print("Enter your URL")
url = input("").strip()

print("Do you want audio or video and audio? [a or v] (a - audio, v - video & audio)")
choice = input("").lower().strip()

if choice == "a":
    format_choice = "bestaudio/best"
elif choice == "v":
    format_choice = "best[ext=mp4]/best"
else:
    raise ValueError("Missing correct input ('a' or 'v')")

os.makedirs("./downloads", exist_ok=True)

ydl_options = {
    "format": format_choice,
    "outtmpl": "./downloads/%(title)s.%(ext)s",
    "noplaylist": True,
    "remote_components": "ejs:github",
}

if choice == "a":
    ydl_options["postprocessors"] = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]


with YoutubeDL(ydl_options) as ydl: # type: ignore
    ydl.download([url])

print("Downloaded")
