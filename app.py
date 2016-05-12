import pytz
import requests
import datetime as dt
import subprocess

def gen_url(datetime, x, y):
    return 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/20d/550/' +\
            datetime.strftime("%Y/%m/%d/%H") + datetime.strftime("%M")[:1] +\
            '000_' + str(x) + '_' + str(y) + '.png'

def get_image():
    tz = pytz.timezone('UTC')

    now = dt.datetime.now(tz)
    now = now.replace(minute=int(str(now.minute)[:1] + '0'))
    now = now.replace(hour=1,day=12)

    frame_num = 0
    frame_length = dt.timedelta(minutes=10)
    for i in range(10):
        img_num = 0
        for y in range(14, 16):
            for x in range(11, 13):
                url = gen_url(now, x, y)
                print(url)
                r = requests.get(url)
                img_num += 1
                with open('img/' + str(img_num).zfill(2) + '.png', 'w') as png:
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

def create_video():
    subprocess.call(['ffmpeg', '-framerate', '5', '-i', 'frames/%02d.png',
                     '-r', '5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                     'out.mp4'])

if __name__ == '__main__':
    get_image()
    create_video()
