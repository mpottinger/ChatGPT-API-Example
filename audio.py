# Record an MP3 file from the microphone
import io
import os
import subprocess
import wave

import pyaudio
from ffmpeg.ffmpeg import FFmpeg # python-ffmpeg

def record_wav(keyboard_queue):
    # Record audio
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 44100  # Record at 44100 samples per second

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print('Recording, press any key to stop...')

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # Store data in chunks until you press a key
    while True:
        # exit if any key is pressed using OpenCV
        # show some text on the image (Press any key to stop recording)
        # show frames from animation.mp4 while waiting for user to press a key
        data = stream.read(chunk)
        frames.append(data)
        # exit if a key is pressed
        if not keyboard_queue.empty():
            k = keyboard_queue.get()
            print('key pressed, stopping recording')
            break

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    print('Finished recording')

    # Save the recorded data as a WAV file, create audio_video folder if it doesn't exist
    if not os.path.exists('audio_video'):
        os.mkdir('audio_video')

    filename = os.path.join('audio_video','microphone_input.wav')
    # remove the old file if it exists
    if os.path.exists(filename):
        os.remove(filename)
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()
    return filename


def convert_to_mp3(filename):
    # convert to MP3
    ffmpeg = (
        FFmpeg()
        .option('y')
        .input(filename)
        .output(filename.replace('.wav', '.mp3'))
    )
    ffmpeg.execute()


def record_mp3(keyboard_queue):
    wav_filename = record_wav(keyboard_queue)
    print('Converting to MP3: ', wav_filename)
    convert_to_mp3(wav_filename)
    filename = wav_filename.replace('.wav', '.mp3')
    return filename
