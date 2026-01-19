"""
This the first processing script, that loads audio from ./teasers.json.

Create python venv and install ffmpeg and other dependencies:

    $ apt update && apt install -y ffmpeg
    or
    $ brew update; brew install ffmpeg

    $ python3 -m venv venv

    $ source ./venv/bin/activate

To load audio without cleaning and segmentation:
    $ pip install yt-dlp  

Dependencies for the full pipeline:
    $ pip install -r requirements.txt
    
Run the loading script
    $ python load_audio.py
"""
import os
import shutil
import yt_dlp
import json


def load_audio(url, cookies=None, subtitles=False):
    ydl_opts = {
        'quiet': True,
        'restrict_filenames': True,
        'windowsfilenames': True,
        'no_warnings': True,
        "outtmpl": '%(title)s.%(ext)s',  # this is where you can edit how you'd like the filenames to be formatted
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '0',
        }, {
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'vtt',
        }],
        'writesubtitles': subtitles,
        'subtitleslangs': ['all'],
        'overwrites': False,
    }
    if cookies is not None:
        print("COOKIES", os.path.exists(cookies))
        ydl_opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        info = ydl.sanitize_info(info)

        def recursive_print(top_key, info_dict):
            for key, info_value in info_dict.items():
                if "file" in key or "name" in key or "title" in key:
                    print(top_key, key, "=", info_value)
                if isinstance(info_value, dict):
                    recursive_print(key, info_value)  
        # recursive_print("top_level", info)
        
        # Remove the extension to get the base filename
        full_filename = ydl.prepare_filename(info)
        filename_base, _ = os.path.splitext(full_filename)
        print("filename_base:", filename_base)

        audio_filename = filename_base + ".wav"
        subs_filenames = []
        if subtitles:
            requested_subs = info.get("requested_subtitles", None)    # 2. Look at what subtitles were actually requested/downloaded
            print("requested_subs", requested_subs)
            if subtitles and requested_subs is None:
                raise RuntimeError(f"No subtitles found")
            languages = requested_subs.keys()
            subs_filenames = []
            for language in requested_subs.keys():
                subs_filenames.append(filename_base + "." + language + ".vtt")

        ydl.download([url])
        return audio_filename, subs_filenames


if __name__ == "__main__":
    print("Loading data from teasers.json ...")
    with open("teasers.json", "r", encoding='utf-8') as f:
        dataset = json.load(f)

    for audio_data in dataset:
        url = audio_data["url"]
        filename = audio_data["filename"]
        audio_filename = audio_data["audio_filename"]

        loaded_audio_filename, _, = load_audio(url, subtitles=False)
        shutil.move(loaded_audio_filename, f"./data/{audio_filename}")
        print("audio loaded:", audio_filename)

    print("---- FINISHED PROCESSING ----")





