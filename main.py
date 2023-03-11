import datetime
import multiprocessing
import shutil
import sys

import time
import openai
import dropbox
import requests

import asyncio
import json

import audio
from audio import *

from show_animation import animation_process

print("Loading libraries...")
from elevenlabslib import *

import pyttsx3
tts = pyttsx3.init()

# *********** CONFIG ***********
from configuration import *

openai.api_key = OPENAI_API_KEY
user = ElevenLabsUser(ELEVENLABS_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# *********** END API KEYS ***********


# check if subscription still has enough credits for ElevenLabs voice synthesis
print("Checking ElevenLabs Speech Synthesis credits...")
chars_used = user.get_current_character_count()
char_limit = user.get_character_limit()
can_extend = user.get_can_extend_character_limit()
monthly_payment = user.get_next_invoice()['amount_due_cents'] / 100
print('ElevenLabs: chars used: ' + str(chars_used))
print('ElevenLabs: char limit: ' + str(char_limit))
print('ElevenLabs: can extend: ' + str(can_extend))
print('ElevenLabs: monthly payment: $' + str(monthly_payment))

# if there are less than 100 characters left, stop the program
if char_limit - chars_used < 100:
    print('Not enough ElevenLabs Speech Synthesis credits left to continue')
    exit()

voice = None
keyboard_queue = multiprocessing.Queue()
videopath_queue = multiprocessing.Queue()

pyaudio_device_id = None

# Change audio device from default. Uncommenting this will list all available audio devices and set the device to use by name.
# p = pyaudio.PyAudio()
# # Device name:
# audio_device = 'Speakers (USB2.0 Device)'
# # audio_device = 'MacBook Pro Speakers'
# pyaudio_device_id = 0
# for i in range(p.get_device_count()):
#     dev = p.get_device_info_by_index(i)
#     print((i, dev['name'], dev['maxInputChannels']))
#     if dev['name'] == audio_device:
#         pyaudio_device_id = i
# print('Using portaudio device id for ElevenLabs streaming speech output: ', pyaudio_device_id)

use_whisper = True

# Keep track of OpenAI API usage and display cost of the session
reply_count = 0
tokens_used = 0

# This is a separate script which simply shows the animated face.
# If the window is closed, this chat program will quit.
anim_proc = None

# Write the pid of this file to main.pid so that anim_proc can terminate this program if the window is closed
with open('main.pid', 'w') as f:
    f.write(str(os.getpid()))


# ChatGPT API call:
# This code defines a function named 'get_reply' that takes a list of messages as input.
# The function calls the OpenAI API using the 'openai.ChatCompletion.create' function to
# generate a response based on the input message.
# The reply from the OpenAI API is stored in the 'reply' variable,
# and the total number of tokens used in the API call is stored in the 'tokens' variable.
# The function then increments the 'tokens_used' global variable by the number
# of tokens used in the API call and calculates the cost of the API call based on the number of tokens used.
# Finally, the function appends the response to the 'messages' list,
# prints the number of tokens used and the cost, and returns the generated reply.
def get_reply(messages):
    global tokens_used
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )
    reply = response['choices'][0]['message']['content']
    tokens = response['usage']['total_tokens']
    # The ChatGPT API costs $0.002 per 1,000 tokens. So we need to keep track of how many tokens we use.
    tokens_used += tokens
    cost = tokens_used / 1000 * 0.002
    print('tokens: ' + str(tokens_used) + ' Total used this session: ' + str(tokens_used) + ' Cost: $' + str(cost))
    messages.append({'role': 'assistant', 'content': reply})
    return reply


# Stream/play audio from ElevenLabs TTS API and save the audio to a file after it's done playing.
def elevenlabs_speak(text):
    while True:
        try:
            if sys.platform == '':
                # On MacOS streaming audio is not working correctly, so use generate_and_play_audio
                voice.generate_and_play_audio(text, pyaudio_device_id)
            else:
                # On Windows/Linu   x, use generate_and_stream_audio for faster playback (less delay)
                voice.generate_and_stream_audio(text, pyaudio_device_id)
            break
        except:
            print('Error connecting to ElevenLabs API, retrying...')
            time.sleep(5)

    voice._bytesFile.seek(0)
    # write the audio to a file
    with open(os.path.join('audio_video', 'chatbot_output.mp3'), 'wb') as f:
        f.write(voice._bytesFile.read())


def pyttsx3_speak(text):
    print('Speaking: ', text)
    tts.say(text)
    tts.runAndWait()



# Upload a file to dropbox and get a shared link.
def share_dropbox(filename):
    with open(filename, 'rb') as f:
        dbx.files_upload(f.read(), '/' + filename, mute=True, mode=dropbox.files.WriteMode.overwrite)

    # share the file via link that can be downloaded via wget,
    shared_link_metadata = dbx.sharing_create_shared_link_with_settings('/' + filename)
    shared_link = shared_link_metadata.url
    # This creates a www.dropbox.com link that can be downloaded
    # via wget or curl so we need to convert it to a dl.dropbox.com link
    shared_link = shared_link.replace('www.dropbox.com', 'dl.dropbox.com')
    # also remove the ?dl=0 at the end
    shared_link = shared_link.replace('?dl=0', '')
    return shared_link


# Create a talking video avatar using the d-id API. (Expensive)
def speak_avatar(text, photo_url):
    # first, delete old video
    try:
        os.remove('avatar.mp4')
    except OSError:
        pass
    # generate the video
    elevenlabs_speak(text)

    # for did live portrait
    # upload audio file to dropbox and get a shared link
    shared_link_audio = share_dropbox(os.path.join('audio_video', 'chatbot_output.mp3'))

    # Set the endpoint URL
    url = 'https://api.d-id.com/talks'

    # Set the request headers
    headers = {
        'Authorization': 'Basic ' + DID_API_KEY,
        'Content-Type': 'application/json'
    }

    # Set the request payload
    payload = {
        'driver_url': 'bank://lively',
        'script': {
            'type': 'audio',
            'audio_url': shared_link_audio
        },
        'source_url': photo_url
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(response)
    if response.status_code != 200 and response.status_code != 201:
        print('error creating avatar: ', response.json())
        quit()

    print(response.json())
    id = response.json()['id']
    # Print the response
    print('creating avatar: ', response.json())

    # wait a few seconds for the avatar to be generated
    time.sleep(3)

    # Set the endpoint URL
    url = 'https://api.d-id.com/talks/' + id

    # Set the request headers
    headers = {
        'Authorization': 'Basic ' + DID_API_KEY,
        'Content-Type': 'application/json'
    }

    while True:
        # Send the GET request
        response = requests.get(url, headers=headers)
        print(response)
        if response.status_code != 200 and response.status_code != 201:
            print('error getting avatar: ', response.json())
            quit()
        # Print the response
        print('avatar created, checking for result url in: ', response.json())
        if 'result_url' in response.json():
            break
        time.sleep(1)

    result_url = response.json()['result_url']  # an mp4 file
    # download the mp4 file
    r = requests.get(result_url, allow_redirects=True)
    open('avatar.mp4', 'wb').write(r.content)
    # play the mp4 file
    #PlayVideo('avatar.mp4')


# Create an animated photo using d-id api.
# This should only be done once per character
# and the file saved as animation.mp4 and placed in the character's directory.
# This animation.mp4 can also be created for free with the https://www.myheritage.com/ website.
def get_animation(photo_url):
    # Set the URL and headers for the API request
    url = 'https://api.d-id.com/animations'
    headers = {
        'Authorization': 'Basic ' + DID_API_KEY,
        'Content-Type': 'application/json'
    }

    # Set the parameters for the API request
    source_url = photo_url
    driver_url = 'bank://fun'
    config = {'mute': True}

    # Send the API request to create the animation
    # Expected Response
    # JSON
    #
    # {
    #    'id':'<id>',
    #    'created_at':'<time>',
    #    'status':'created',
    #    'object':'animation'
    # }

    response = requests.post(url, headers=headers, json={
        'source_url': source_url,
        'driver_url': driver_url,
        'config': config
    })
    print(response)
    # Check if the request was successful
    if response.status_code == 201 or response.status_code == 200:
        id = response.json()['id']
        print('Animation created, id:', id)
        # Send the API request to check the status of the animation and get the result URL
        # Expected Response
        # JSON
        #
        # {
        #    'result_url':'<result_url>',
        #    'metadata':{...},
        #    'source_url':'https://.../david.jpg',
        #    'status':'done',
        #    'driver_url':'bank://...',
        #    'modified_at':'<time>',
        #    'user_id':'<user_id>',
        #    'id':'<id>',
        #    'started_at':'<time>'
        # }
        while True:
            response = requests.get(url + '/' + id, headers=headers)
            if response.status_code != 200:
                print('error getting animation: ', response.json())
                quit()
            # Print the response
            print('animation created, checking for result url in: ', response.json())
            if 'result_url' in response.json():
                break
            time.sleep(1)
        # Get the result URL
        result_url = response.json()['result_url']
        print('Animation result URL:', result_url)
        # download the mp4 file
        r = requests.get(result_url, allow_redirects=True)
        open(os.path.join(CHARACTER, 'animation.mp4'), 'wb').write(r.content)
        # play the mp4 file
        # PlayVideo('animation.mp4')
    else:
        print(f'Error: {response.status_code} - {response.text}')


# transcribe an MP3 file using OpenAI Whisper API
def transcribe_audio():
    audio_file = open(os.path.join('audio_video', 'microphone_input.mp3'), 'rb')
    # make sure the audio file is not empty and is long than Minimum audio length is 0.1 seconds.
    audio_file.seek(0, 2)
    if audio_file.tell() == 0:
        audio_file.close()
        return '..... silence'
    audio_file.seek(0)

    while True:
        try:
            transcript = openai.Audio.transcribe(model='whisper-1', file=audio_file,
                                                 prompt="Umm, let me think like, hmm... Okay, here's what I'm, like, thinking.")[
                'text']
            break
        except openai.error.InvalidRequestError as e:
            print('Audio file is too short, retrying, returning silence: ', e)
            return '..... silence'
        except Exception as e:
            print('error transcribing audio, retrying: ', e)
            time.sleep(5)
    audio_file.close()
    return transcript


# Get user input either via the keyboard or via whisper
def get_input(prompt='You: '):
    global use_whisper

    print('get_input: use_whisper: ', use_whisper)
    if use_whisper:
        print('Using Whisper Speech to Text, press any key start/stop recording, esc to exit')
        # check keyboard queue for keypress, if esc is pressed then exit
        k = keyboard_queue.get()
        if k == 27:
            print('Exiting...')
            return None
        audio.record_mp3(keyboard_queue)

        # check if animation window is closed
        if not anim_proc.is_alive():
            print('Animation process terminated, exiting...')
            return None
        transcript = transcribe_audio()
        print('Transcript: ', transcript)
        return transcript
    else:
        return input(prompt)


if __name__ == '__main__':

    # kill existing animation processes
    try:
        with open('animation.pid', 'r') as f:
            pid = int(f.read())
            print('killing animation process: ', pid)
            # wait until it has been killed
            while True:
                try:
                    os.kill(pid, 0)
                except Exception as e:
                    print('animation process killed: ', e)
                    break
                time.sleep(1)
                print('waiting for animation process to terminate...')
    except:
        pass

    print('Getting voice: ', VOICE_NAME)
    voice = user.get_voices_by_name(VOICE_NAME)[0]  # This is a list because multiple voices can have the same name
    print('voice: ', voice)

    # speak_avatar('This is a test', photo_url) # test speaking video avatar using d-id api.

    # delete old audio/video input/output files in current directory in a cross platform way (mp3, wav, mp4)
    try:
        for f in os.listdir('.'):
            if f.endswith('.mp3') or f.endswith('.wav') or f.endswith('.mp4'):
                os.remove(f)
    except:
        pass

    while True:
        try:
            if os.path.exists('audio_video'):
                # delete the audio_video folder in cross platform way
                shutil.rmtree('audio_video')
            os.makedirs('audio_video')
            os.makedirs(os.path.join('audio_video', 'output'))
            break
        except:
            print('audio_video folder still exists, waiting for old animation process to terminate...')
            time.sleep(1)

    # Get the photo of the character from photo.jpg (only used for the video avatar, which is disabled for now)
    # if the character doesn't have an animation.mp4 file, then create one
    if not os.path.exists(os.path.join(CHARACTER, 'animation.mp4')):
        photo_file = CHARACTER + '/photo.jpg'
        photo_url = share_dropbox(photo_file)
        get_animation(photo_url) # get animation.mp4 for a new avatar image

    # copy animation.mp4 to to the output folder
    animation_src_path = os.path.join(CHARACTER, 'animation.mp4')
    animation_dst_path = os.path.join('audio_video', 'output', 'animation.mp4')
    shutil.copy(animation_src_path, animation_dst_path)

    # start the animation using multiprocessing so it can run in the background as a daemon process
    print('starting animation process...')
    anim_proc = multiprocessing.Process(target=animation_process, args=(keyboard_queue,videopath_queue,))
    anim_proc.daemon = True
    anim_proc.start()


    messages = []  # This will hold the conversation history
    # Load character's personality from personality.txt
    with open(os.path.join(CHARACTER, 'personality.txt'), 'r') as f:
        personality = f.read()

    # Get the Name of the character from first line of personality.txt format is eg: Name: Jason Pottinger
    full_name = personality.splitlines()[0].split(':')[1].strip()
    print('Full Name: ', full_name)

    system_message = personality  # System message defines some background information about the character
    # Append current date and time to the system message
    system_message += 'Current date and time: ' + datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")

    messages.append({'role': 'system', 'content': system_message})

    # Add some initial back/forth dialogue
    # to establish the identity of the character and give ChatGPT some context
    message = "Hello! Who are you?"
    messages.append({'role': 'user', 'content': message})
    assistant_message = "Well, um, I am: " + system_message
    messages.append({'role': 'assistant', 'content': assistant_message})
    message = "That's cool! So now I understand that you are " + full_name + ". Ok, let's start chatting and you play the role of " + full_name + " and stay in that role, speaking naturally, just as you would in real life."
    messages.append({'role': 'user', 'content': message})
    assistant_message = "Ok, so uh, let's start chatting and I will play the role of " + full_name + " and stay in that role. I will emulate their speech realistically and naturally (including a lot of uhs and umms to be realistic) , personality and their interests/likes/dislikes, etc."
    messages.append({'role': 'assistant', 'content': assistant_message})

    # Main loop
    # When done you can run combine_output.py to combine the audio and video files into a single mp4 file
    # combined output will be placed in combined_output folder.
    pyttsx3_speak('Starting. Press a key to start recording and press again to stop.')
    pyttsx3_speak('First, tell me your name.')
    user_name = get_input('Tell us your name. ')  # Get user name
    if user_name is None:
        sys.exit(0)
    pyttsx3_speak('Ok, ' + user_name + ', let\'s start chatting. Press a key to start recording and press again to stop.')
    while True:
        # check if animation process is still running
        if not anim_proc.is_alive():
            print('Animation process has terminated, exiting...')
            break
        print('messages: ', len(messages))
        user_input = get_input('You: ')  # Get user input (either via microphone with Whisper API, or keyboard)
        if user_input is None:
            break
        message = user_name + ': ' + user_input  # Add user name to message

        messages.append({'role': 'user', 'content': message})  # add user message to messages list
        reply = get_reply(messages)  # Get the reply from ChatGPT API
        print(reply)
        # remove the text before the : from the reply (eg: Jason: Hello, how are you? -> Hello, how are you?) but keep the rest of the reply including : and spaces
        reply = reply[reply.find(':') + 1:]


        elevenlabs_speak(reply)  # ElevenLabs API for streaming text to speech only (no video, macos)
        #pyttsx3_speak(reply)  # local tts (faster, but low quality)

        # Note: Talking Avatar API is not used in this example but code is included for reference
        # The reason is that it is very expensive. Only useful for demo purposes but not
        # for longer term use. Instead, it's more economical to just create an animation.mp4
        # This can be done via the d-id API
        # or going to the https://www.myheritage.com/ website and creating for free.
        # speak_avatar(reply, photo_url) # d-id API for streaming text to speech with video

        reply_count += 1
        # copy the mic audio and the reply audio/video files to the output folder, and append transcript to conversation.txt
        shutil.copy(os.path.join('audio_video', 'microphone_input.mp3'),
                    os.path.join('audio_video', 'output', 'microphone_input_' + str(reply_count) + '.mp3'))
        shutil.copy(os.path.join('audio_video', 'chatbot_output.mp3'),
                    os.path.join('audio_video', 'output', 'chatbot_output_' + str(reply_count) + '.mp3'))

        # Uncomment the following line to copy the avatar video file to the output folder (disabled by default, too expensive)
        # shutil.copy('avatar.mp4', os.path.join('audio_video','output','avatar_' + str(reply_count) + '.mp4'))

        # Conversation is formatted as 'User: message\nAI: reply\n\n'
        conversation_history = 'User: ' + message + '\nAI: ' + reply + '\n\n'

        # append to conversation.txt
        with open(os.path.join('audio_video', 'output', 'conversation.txt'), 'a') as f:
            f.write(conversation_history)
