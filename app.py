import os
import pytz
import requests
import datetime as dt
import subprocess
import hashlib


class SingleFrame(object):
    def __init__(self, datetime, x_range, y_range, tmp_folder, output_path):
        self.dt = datetime
        self.x_range = x_range
        self.y_range = y_range
        self.tmp_folder = tmp_folder
        self._output_path = output_path

        self.created = False
    
    def create_frame(self):
        if self.created:
            return

        img_num = 0
        for y in self.x_range:
            for x in self.y_range:
                img = SingleImage(self.dt, x, y)

                img_name = str(img_num).zfill(3) + '.png'
                img_path = os.path.join(self.tmp_folder, img_name)
                with open(img_path, 'w') as png_file:
                    png_file.write(img.get_image())

                print('wrote: ' + img_name)

                img_num += 1

        subprocess.call(['montage', '-mode', 'concatenate', '-tile', '2x2',
            os.path.join(self.tmp_folder, '*.png'), self._output_path])

        print('created frame: ' + self._output_path)
        

    
    def get_frame(self):
        create_frame()
        return self._output_path


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


def gen_url(datetime, x, y):
    return 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/20d/550/' +\
            datetime.strftime("%Y/%m/%d/%H") + datetime.strftime("%M")[:1] +\
            '000_' + str(x) + '_' + str(y) + '.png'

def run():
    now = dt.datetime.now(pytz.timezone('UTC'))
    now = now.replace(hour=2)

    f = SingleFrame(now, [14, 15], [11, 12], '/home/nafis/himawari8/app/img',
            '/home/nafis/himawari8/app/frames/001.png')
    f.create_frame()


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

def check_no_img(img_path):
    no_img_hash = r'142dc29d84424bbd305c14168454024a1f758047'
    with open(img_path) as f:
        h = hashlib.sha1(f.read()).hexdigest()
        return no_img_hash == h

def create_video():
    subprocess.call(['ffmpeg', '-framerate', '5', '-i', 'frames/%02d.png',
                     '-r', '5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                     'out.mp4'])

if __name__ == '__main__':
    #get_image()
    #create_video()
    run()
