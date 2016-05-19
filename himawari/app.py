import os
import pytz
import requests
import datetime as dt
import subprocess
import hashlib
import binascii
import shutil
import time
import sys


class SingleFrame(object):
    def __init__(self, datetime, x_range, y_range, frame_folder):
        self.dt = datetime
        self.x_range = x_range
        self.y_range = y_range
        self.base_folder = frame_folder

        self.tmp_folder = os.path.join(frame_folder, 'img')
        self.output_folder = os.path.join(frame_folder, 'out')
        self._output_path = os.path.join(self.output_folder, 'frame.png')

        self.created = False
        self.no_img = False
    
        os.makedirs(self.tmp_folder)
        os.makedirs(self.output_folder)

    def create_frame(self):
        if self.created:
            return

        img_num = 0
        for y in self.y_range:
            for x in self.x_range:
                img = SingleImage(self.dt, x, y)

                img_name = str(img_num).zfill(3) + '.png'
                img_path = os.path.join(self.tmp_folder, img_name)
                
                if img.is_no_img():
                    self.no_img = True
                    return

                with open(img_path, 'wb') as png_file:
                    png_file.write(img.get_image())

                img_num += 1


        self.montage_images()
        self.created = True
        self.no_img = False
        print('created frame: ' + str(self.dt))

        self.set_brightness_contrast()
        self.add_timestamp()
    
    def get_frame(self):
        self.create_frame()

        if self.created:
            return self._output_path

        return False
    
    def is_no_img(self):
        if self.created == False:
            self.create_frame()

        return self.no_img

    def set_brightness_contrast(self):
        subprocess.call(['convert', self.get_frame(), '-brightness-contrast',
            '+15x+20', self.get_frame()])

    def montage_images(self):
        subprocess.call(['montage', '-mode', 'concatenate', '-tile', '2x2',
            os.path.join(self.tmp_folder, '*.png'), self._output_path])

    def add_timestamp(self):
        qld = pytz.timezone('Australia/Queensland')
        q_time = self.dt.astimezone(qld)

        subprocess.call(['convert', self.get_frame(), '-fill', 'white',
            '-pointsize', '24', '-undercolor', '#00000080', '-gravity',
            'South', '-annotate', '+0+5', q_time.strftime('%H:%M')[:-1] + '0 '
            + q_time.strftime('%Z'), self.get_frame()])

    def clean(self):
        shutil.rmtree(self.base_folder)



class SingleImage(object):
    def __init__(self, datetime, x, y):
        self.dt = datetime
        self.x = x
        self.y = y
        self.img = None

    def get_image(self):
        if self.img == None:
            url = self.gen_url(self.dt, self.x, self.y)
            r = requests.get(url)
            self.img = r.content

        return self.img
    
    def is_no_img(self):
        no_img_hash = r'142dc29d84424bbd305c14168454024a1f758047'
        img_hash = hashlib.sha1(self.get_image()).hexdigest()

        return img_hash == no_img_hash


    def gen_url(self, datetime, x, y):
        return 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/20d/550/' +\
                datetime.strftime("%Y/%m/%d/%H") + datetime.strftime("%M")[:1] +\
                '000_' + str(x) + '_' + str(y) + '.png'

def create_video(frames, video_frames_dir, output_path):

    if os.path.exists(video_frames_dir):
        shutil.rmtree(video_frames_dir)
    os.mkdir(video_frames_dir)

    frame_num = 0

    for frame in reversed(frames):

        if frame.is_no_img():
            continue

        frame_path = frame.get_frame()
        frame_out_path = os.path.join(video_frames_dir,
                str(frame_num).zfill(3) + '.png')

        shutil.copyfile(frame_path, frame_out_path)

        frame_num += 1

    subprocess.call(['ffmpeg', '-y', '-nostats', '-loglevel', '0', '-framerate',
        '5', '-i', os.path.join(video_frames_dir, '%03d.png'), '-r', '5',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', output_path])

def gen_rand_folder(base_path):
    folder_name = binascii.hexlify(os.urandom(8)).decode()


    folder_path = os.path.join(base_path, folder_name)

    if os.path.exists(folder_path):
        return rand_folder_gen(base_path)

    return folder_path


def tracker(hours, base_dir):
    x_range = [11, 12]
    y_range = [14, 15]

    frames_folder = os.path.join(base_dir, 'data', 'frames')
    if os.path.exists(frames_folder):
        shutil.rmtree(frames_folder)
    os.makedirs(frames_folder)

    video_frames_dir = os.path.join(base_dir, 'data', 'video_frames')

    video_path = os.path.join(base_dir, 'data', 'out.mp4')

    time_interval = dt.timedelta(minutes=10)
    frame_time = dt.datetime.now(pytz.timezone('UTC'))

    # latest frame in 0th index, oldest at the end of list
    frames = []

    num_frames = int(hours * 6)

    # create intial frames
    for i in range(1, num_frames + 1):
        rand_folder = gen_rand_folder(frames_folder)
        frame = SingleFrame(frame_time - time_interval * i, x_range, y_range, rand_folder)
        frames.append(frame)

    while True:
        old_frame = frames.pop()
        old_frame.clean()
        rand_folder = gen_rand_folder(frames_folder)
        print('frame_time', frame_time)
        frame = SingleFrame(frame_time, x_range, y_range, rand_folder)
        frames = [frame] + frames

        print('frames length: ' + str(len(frames)))

        print('creating video')

        create_video(frames, video_frames_dir, video_path)

        print('created video, waiting 10 minutes')
        print('-----------------------------------------')
        time.sleep(60 * 10)
        frame_time = frame_time + time_interval


if __name__ == '__main__':

    base_dir = os.path.realpath(os.path.join(
        os.path.dirname(os.path.realpath(sys.argv[0])), '..'))

    tracker(2, base_dir)
