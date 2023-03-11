import time

import cv2
import os
from ffpyplayer.player import MediaPlayer

# Play the animation in a separate process in OpenCV.
# Make sure there is only a single instance of the animation running
# If there is already an instance running, terminate it


# Play a video file. Usually used for d-id talking avatar API result.
# Not currently used in this script because d-id api is too expensive.
# Only here as a reference.
def PlayVideo(video_path, window_name):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    player = MediaPlayer(video_path)
    start_time = time.time() * 1000  # start time in milliseconds
    while True:
        grabbed, frame = video.read()
        audio_frame, val = player.get_frame()
        if not grabbed:
            print('End of video')
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.imshow(window_name, frame)
        if val != 'eof' and audio_frame is not None:
            # audio
            img, t = audio_frame
            # calculate expected time
            expected_time = start_time + video.get(cv2.CAP_PROP_POS_MSEC)
            # wait until expected time
            while time.time() * 1000 < expected_time:
                time.sleep(0.001)


def start_video(video_filepath):
    print('Playing video: ', video_filepath)
    cap = cv2.VideoCapture(video_filepath)
    # get frame rate of the video
    fps = cap.get(cv2.CAP_PROP_FPS)
    # get the total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # calculate the duration of the video
    duration = total_frames / fps
    # calculate time to wait between frames
    wait_time = int(1000 / fps)
    return cap, wait_time



def animation_process(keyboard_queue,filepath_queue):

    # check if there is a file called animation.pid
    if os.path.exists('animation.pid'):
        # if there is a file called animation.pid, read the pid from the file
        with open('animation.pid', 'r') as f:
            pid = f.read()
        try:
            os.kill(int(pid), 0)
        except Exception as e:
            # if the pid in the file is not running, delete the file
            os.remove('animation.pid')

    # if there is no file called animation.pid, create a file called animation.pid and write the pid to the file
    pid = os.getpid()
    with open('animation.pid', 'w') as f:
        f.write(str(pid))

    # create a window to display the video and make it active
    window_name = 'ChatGPT: Press ESC to exit, any other key or mouse click to start/stop recording'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    # allow mouse events
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            keyboard_queue.put(32)
        if event == cv2.EVENT_RBUTTONDOWN:
            keyboard_queue.put(32)
    cv2.setMouseCallback(window_name, mouse_callback)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    # read the pid of main.py from the file main.pid
    try:
        with open('main.pid', 'r') as f:
            pid = int(f.read())
    except Exception as e:
        print('Could not read pid from file main.pid')
        print(e)
        exit()


    video_filepath = os.path.join('audio_video', 'output', 'animation.mp4')
    cap, wait_time = start_video(video_filepath)
    # loop through the video
    # this is run in a separate process, loop forever playing the animation
    while True:
        # check if a new filepath has been added to the queue
        if not filepath_queue.empty():
            # if a new filepath has been added to the queue, get the filepath from the queue
            # make sure it is a different filepath
            # if it is the same filepath, do nothing
            # if it is a different filepath, stop playing the current video and start playing the new video
            new_video_filepath = filepath_queue.get()
            if new_video_filepath == video_filepath:
                print('Filepath is the same as the current video, skipping')
                continue
            video_filepath = new_video_filepath
            cap.release()
            # start playing the video
            cap, wait_time = start_video(video_filepath)

        ret, img = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        cv2.imshow(window_name, img)
        # if user hit any key, send it to the keypress queue
        k = cv2.waitKey(wait_time)
        if k != -1:
            print('Key pressed: ', k)
            keyboard_queue.put(k)
        # if the user hit the escape key, exit and terminate the parent process
        if k == 27:
            break

    # release the video capture object
    cap.release()
    # destroy the window
    cv2.destroyAllWindows()

    # terminate the parent process
    os.kill(pid, 9)

    # delete the file animation.pid
    try:
        os.remove('animation.pid')
        os.remove('main.pid')
    except Exception as e:
        print(e)






