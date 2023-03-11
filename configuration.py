# *********** CONFIG ***********
# *********** API KEYS ***********
# Enter your API Keys here...
# Place your OpenAI API key here
OPENAI_API_KEY = '<your key here>'

# ElevenLabs API key
ELEVENLABS_API_KEY = '<your key here>'

# Place your d-id API key here (optional). An animated photo could also be created at http://myheritage.com
DID_API_KEY = '<your key here>'

# Dropbox access token
DROPBOX_ACCESS_TOKEN = '<your access token here>' # Only used for d-id API and not essential


CHARACTER = 'trump'  # Change this to your character name
# for voice in user.get_available_voices():
#    print(voice.get_name())
VOICE_NAME = '<ElevenLabs API voice name>'  # Change this to your voice name in ElevenLabs


# Check that configuration has been set for all the required keys

if OPENAI_API_KEY == '<your key here>' or ELEVENLABS_API_KEY == '<your key here>' or VOICE_NAME == '<ElevenLabs API voice name>':
    print('Please enter your API keys and ElevenLabs voice name in configuration.py')
    exit()