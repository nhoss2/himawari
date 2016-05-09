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
    now = now.replace(hour=23,day=5)

    frame_num = 0
    frame_length = dt.timedelta(minutes=10)
    for i in range(10):
        img_num = 0
        for y in range(13, 17):
            for x in range(10, 14):
                url = gen_url(now, x, y)
                print url
                r = requests.get(url)
                img_num += 1
                with open('img/' + str(img_num).zfill(2) + '.png', 'w') as png:
                    png.write(r.content)

        subprocess.call(['montage', '-mode', 'concatenate', '-tile', '4x4', 
                         'img/*.png','frames/' + str(frame_num).zfill(2) + '.png'])
        frame_num += 1
        now = now + frame_length
        print(now)


if __name__ == '__main__':
    get_image()
