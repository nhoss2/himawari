import os
import pytz
import requests
import datetime as dt
import subprocess
import hashlib
import binascii
import shutil
import time


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

                with open(img_path, 'w') as png_file:
                    png_file.write(img.get_image())

                img_num += 1


        self.montage_images()
        self.created = True
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
            'South', '-annotate', '+0+5', q_time.strftime('%H:%M %Z'),
            self.get_frame()])

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
            url = gen_url(self.dt, self.x, self.y)
            r = requests.get(url)
            self.img = r.content

        return self.img
    
    def is_no_img(self):
        no_img_hash = r'142dc29d84424bbd305c14168454024a1f758047'
        img_hash = hashlib.sha1(self.get_image()).hexdigest()

        return img_hash == no_img_hash


def gen_url(datetime, x, y):
    return 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/20d/550/' +\
            datetime.strftime("%Y/%m/%d/%H") + datetime.strftime("%M")[:1] +\
            '000_' + str(x) + '_' + str(y) + '.png'

def get_image():
    tz = pytz.timezone('UTC')

    now = dt.datetime.now(tz)
    now = now.replace(minute=int(str(now.minute)[:1] + '0'))
    now = now.replace(hour=0,day=16)

    frame_num = 0
    frame_length = dt.timedelta(minutes=10)
    for i in range(20):
        img_num = 0
        for y in range(14, 16):
            for x in range(11, 13):
                url = gen_url(now, x, y)
                print(url)
                r = requests.get(url)
                img_num += 1
                img_name = str(img_num).zfill(2) + '.png'
                with open('img/' + img_name, 'w') as png:
                    png.write(r.content)

        frame_name = str(frame_num).zfill(2) + '.png'

        subprocess.call(['montage', '-mode', 'concatenate', '-tile', '2x2',
                         'img/*.png','frames/' + frame_name])

        subprocess.call(['convert', 'frames/' + frame_name, '-brightness-contrast', '+15x+20',
                        'frames/' + frame_name])

        qld = pytz.timezone('Australia/Queensland')
        q_time = now.astimezone(qld)

        subprocess.call(['convert', 'frames/' + frame_name,
        '-fill', 'white', '-pointsize', '18', '-undercolor',
        '#00000080', '-gravity', 'South', '-annotate', '+0+5',
        q_time.strftime('%H:%M %Z'), 'frames/' + frame_name])

        frame_num += 1
        now = now + frame_length
        print(now)

def create_video(frames):

    video_frames_dir = '/home/nafis/himawari8/app/video_frames'

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

    subprocess.call(['ffmpeg', '-y', '-framerate', '5', '-i',
        os.path.join(video_frames_dir, '%03d.png'), '-r', '5', '-c:v',
        'libx264', '-pix_fmt', 'yuv420p', 'out.mp4'])

def gen_rand_folder(base_path):
    folder_name = binascii.hexlify(os.urandom(8))

    folder_path = os.path.join(base_path, folder_name)

    if os.path.exists(folder_path):
        return rand_folder_gen(base_path)

    return folder_path


def tracker(hours):
    x_range = [11, 12]
    y_range = [14, 15]

    frames_folder = '/home/nafis/himawari8/app/frames'

    time_interval = dt.timedelta(minutes=10)
    frame_time = dt.datetime.now(pytz.timezone('UTC'))

    # latest frame in 0th index, oldest at the end of list
    frames = []

    num_frames = hours * 6

    for i in range(num_frames):
        rand_folder = gen_rand_folder(frames_folder)
        frame = SingleFrame(frame_time, x_range, y_range, rand_folder)
        frames.append(frame)

        frame_time = frame_time - time_interval

    while True:
        old_frame = frames.pop()
        old_frame.clean()
        rand_folder = gen_rand_folder(frames_folder)
        frame_time = dt.datetime.now(pytz.timezone('UTC'))
        print('frame_time', frame_time)
        frame = SingleFrame(frame_time, x_range, y_range, rand_folder)
        frames.insert(0, frame)

        print 'creating video'
        create_video(frames)

        print 'created video, waiting 10 minutes'
        time.sleep(60 * 10)


 


if __name__ == '__main__':
    tracker(3)
