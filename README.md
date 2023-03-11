ChatGPT + Whisper + ElevenLabs TTS

---------------------------

Quick Start:
install requirements first using pip3 install -r requirements.txt
then edit configuration.py and add your API keys, etc.
create a voice on the ElevenLabs TTS website and add the voice name to configuration.py

Simple example of using ChatGPT API with Whisper API, and ElevenLabs TTS API.

Enter your API keys and other config in configuration.py

Run the script with python3 main.py or flask_app.py

combine_output will combine the output of the chat session from main.py into a single video file

Every character has their own folder with animation.mp4, personality.txt and photo.jpg
personality.txt is the system message/prompt for the chat session

The first line of personality.txt has the name,
formatted as Name: <name>

animation.mp4 can be created by d-id automatically from photo.jpg when main.py is run
or you can produce your own and place it in the folder.

Previously I had used d-id speaking avatar animations but that's very expensive for this purpose.
The code is there, but it is disabled.

This is a quick and dirty example.
This code is provided as-is, and is not meant to be used in production. 

It is only for reference.
No support will be provided for this code, it is in an unfinished state as I am not actively working on it and it is merely a starting point.


