import os
import shutil

import cv2
from ffmpeg import FFmpeg # python-ffmpeg


# *********** Combine the video and audio files from the last chat session into a single video file ***********
# Run this script to make a full video of the last chat session
# Final result will be stored in combined_output/combined_video.mp4
# Temporary files are deleted after the final video is created

def get_video_length(filename):
    import subprocess, json
    print(filename)
    result = subprocess.check_output(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename])

    #print(result)
    fields = json.loads(result)['streams'][0]

    duration = fields['duration']
    fps      = eval(fields['r_frame_rate'])
    return duration


def get_audio_length(filename):
    import subprocess, json
    print(filename)
    result = subprocess.check_output(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename])
    print(result)
    fields = json.loads(result)['streams'][0]

    duration = fields['duration']
    return duration


# use OpenCV to create a looping video of a given length
def create_looping_video(input_file, output_file, length):

    # read the input video file
    cap = cv2.VideoCapture(input_file)

    # get the frame rate of the input video file
    fps = cap.get(cv2.CAP_PROP_FPS)

    # get the total number of frames in the input video file
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # calculate the number of frames to loop
    print('length: ', length)
    print('fps: ', fps)
    loop_frames = int(float(fps) * float(length))

    # calculate the number of times to loop the video
    loop_count = int(loop_frames / total_frames)

    # calculate the number of frames to add to the end of the video
    end_frames = loop_frames - (loop_count * total_frames)

    # create a list to store the frames
    frames = []

    # loop through the video and store the frames in the list
    while True:
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        else:
            break

    # now loop through the list and add the frames to the output video
    # create a video writer object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (frames[0].shape[1], frames[0].shape[0]))

    # loop through the list and add the frames to the output video
    for i in range(loop_count):
        for frame in frames:
            out.write(frame)

    # add the end frames to the output video
    for i in range(end_frames):
        out.write(frames[i])

    # release the video writer object
    out.release()

    # release the video capture object
    cap.release()

def combine_output(i):
    print('reply_count: ', i)
    # combine the audio and video files into a single video file, use animation.mp4(video only) and microphone_input.mp3(audio) for when the user is speaking,
    # and avatar.mp4 for when the AI is speaking
    # loop through the output folder and combine the audio and video files into a single video file
    # write the final video to combined_output.mp4

    # create a new folder to store the combined audio and video files
    # clear the old folder if it exists
    if os.path.exists('combined_output'):
        shutil.rmtree('combined_output')
    os.mkdir('combined_output')

    # loop through the output folder and combine the audio and video files into a single video file for user audio and background video
    print('i: ', i)
    # combine the audio and video files into a single video file, use animation.mp4(video only) and microphone_input.mp3(audio) for when the user is speaking,
    # and chatbot_output_(i).mp3 and animation.mp4 for when the AI is speaking

    # add audio to the user video (microphone_input.mp3) and the animation video (animation.mp4), cut animation.mp4 to the length of the audio
    # extend/loop animation.mp4 to the length of the audio or cut the audio to the length of the animation.mp4

    # first check if the audio file is longer than the video file, if the audio file is longer, extend/loop the video file to the length of the audio file
    audio_length = get_audio_length(os.path.join('audio_video','output', 'microphone_input_' + str(i) + '.mp3'))
    create_looping_video(os.path.join('audio_video','output', 'animation.mp4'), os.path.join('combined_output', 'combined_input' + str(i) + '.mp4'), audio_length)

    # Add the audio to the combined video file
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(os.path.join('combined_output', f'combined_input{i}.mp4'))
        .input(os.path.join('audio_video','output', f'microphone_input_{i}.mp3'))
        .output(os.path.join('combined_output', f'combined_input_audio{i}.mp4'))
    )
    ffmpeg.execute()


    # combine the audio and video files into a single video file, use animation.mp4(video only) and microphone_input.mp3(audio) for when the user is speaking,
    # and chatbot_output_(i).mp3 and animation.mp4 for when the AI is speaking
    # add audio to the user video (microphone_input.mp3) and the animation video (animation.mp4), cut animation.mp4 to the length of the audio
    # extend/loop animation.mp4 to the length of the audio or cut the audio to the length of the animation.mp4

    # first check if the audio file is longer than the video file, if the audio file is longer, extend/loop the video file to the length of the audio file
    audio_length = get_audio_length(os.path.join('audio_video','output', f'chatbot_output_{i}.mp3'))
    create_looping_video(os.path.join('audio_video','output', 'animation.mp4'),
                         os.path.join('combined_output', f'combined_output{i}.mp4'), float(audio_length))

    # Add the audio to the combined video file
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(os.path.join('combined_output', f'combined_output{i}.mp4'))
        .input(os.path.join('audio_video','output', f'chatbot_output_{i}.mp3'))
        .output(os.path.join('combined_output', f'combined_output_audio{i}.mp4'))
    )
    ffmpeg.execute()

def process_output_file(i):
    print('processing output file: ', i)
    combine_output(i)
def finalize_output():
    # combine the video files into a single video file using concat. Use python-ffmpeg to combine the video files instead of ffmpeg and txt file
    # create a list to store the video files
    video_files = []
    for i in range(1, reply_count + 1):
        video_files.append(os.path.join('combined_output', f'combined_input_audio{i}.mp4'))
        video_files.append(os.path.join('combined_output', f'combined_output_audio{i}.mp4'))
    ffmpeg = FFmpeg().option("y")

    for file in video_files:
        print('file: ', file)
        ffmpeg = ffmpeg.input(file)
    # output combined files to combined_output(currentdate/time).mp4 with concat filter the file has the current date and time appended to the file name
    ffmpeg = ffmpeg.output('combined_output.mp4', {
        "filter_complex": "concat=n=" + str(len(video_files)) + ":v=1:a=1"
    })
    ffmpeg.execute()

    # delete the temporary files
    shutil.rmtree('combined_output')
    shutil.rmtree('audio_video')

if __name__ == '__main__':
    from multiprocessing import Pool
    # count the number of files in the output folder that start with chatbot_output_
    reply_count = len([name for name in os.listdir(os.path.join('audio_video','output')) if name.startswith('chatbot_output_')])
    # combine the audio and video files into a single video file

    # create a pool of worker processes
    pool = Pool()

    # distribute the work using the map function
    pool.map(process_output_file, range(1, reply_count + 1))

    # close the pool and wait for the work to complete
    pool.close()
    pool.join()

    # combine the video files into a single video file
    finalize_output()