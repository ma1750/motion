# -*- coding: utf-8 -*-
import glob
import json
import subprocess

import cv2

import math

# (x,y)を中心に1辺paddingの正方形を抽出し
# magnification倍に拡大したものを上書きして描画したデータを返す
def expandation(img, y, x, padding, magnification):
    # img = cv2.imread(img_path)
    h, w = img.shape[:2]
    padding //= 2

    x_lb = max(x-padding, 0)
    x_ub = min(x+padding, w-1)
    y_lb = max(y-padding, 0)
    y_ub = min(y+padding, h-1)

    selected_img = img[y_lb:y_ub, y_lb:y_ub]

    expanded_img = cv2.resize(selected_img, (int((y_ub-y_lb)*magnification), int((x_ub-x_lb)*magnification)))
    padding = int(padding*magnification)

    x_lb = max(x-padding, 0)
    x_ub = min(x+padding, w-1)
    y_lb = max(y-padding, 0)
    y_ub = min(y+padding, h-1)

    yy, xx = img[y_lb:y_ub, x_lb:x_ub].shape[:2]
    e_h, e_w = expanded_img.shape[:2]
    try :
        img[y_lb:y_ub, x_lb:x_ub] = expanded_img[(e_h-yy):e_h, (e_w-xx):e_w]
    except ValueError:
        cv2.imwrite("./y{}_x{}.png".format(y, x), expanded_img)
        #print('y_lb{}, y_ub{}, x_lb{}, x_ub{}\n'.format(y_lb, y_ub, x_lb, x_ub))
    return img

# positions配列のlabelという名前の要素について
# id+1番目とid番目の距離を返す
def get_distance(positions, id, label):
    return math.sqrt(math.fabs((positions[id+1].get(label)[1] - positions[id].get(label)[1])**2 \
    - (positions[id+1].get(label)[0] - positions[id].get(label)[0])**2))


# video_pathが指すvideoから
# 1辺side_lengthの正方形を選択し
# magnification倍したvideoを書き出す
def expand_video(video_path, side_length, magnification):
    positions = []

    dirpath = "./video_hand/"
    frame_length = len(glob.glob(dirpath+"*.json"))

    for i in range(frame_length):
        tmp = None
        with open('./video_hand/{}.json'.format(i), 'r') as f:
            tmp = json.load(f)

        body = tmp.get('people')[0].get('pose_keypoints_2d')

        m_pos = {
            'head'   : (body[0*3], body[0*3+1]),
            'r_hand' : (body[4*3], body[4*3+1]),
            'l_hand' : (body[7*3], body[7*3+1]),
            'l_leg'  : (body[21*3], body[21*3+1]),
            'r_leg'  : (body[24*3], body[24*3+1])
        }
        positions.append(m_pos)

    fuck = []
    max_positions = []
    for i in range(frame_length-1):
        distance = {
            'head'   : get_distance(positions, i, 'head'),
            'r_hand' : get_distance(positions, i, 'r_hand'),
            'l_hand' : get_distance(positions, i, 'l_hand'),
            'l_leg'  : get_distance(positions, i, 'l_leg'),
            'r_leg'  : get_distance(positions, i, 'r_leg'),
        }
        max_distance = max((v, k) for k, v in distance.items())[1]
        fuck.append(max_distance)
        max_positions.append(positions[i].get(max_distance))
    
    with open('max_parts.txt', 'w') as f:
        for i in fuck:
            f.write('{}\n'.format(i))

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    i = 0
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter('video_out.mp4', fourcc, 30, (1920, 1080))

    for i in range(frame_length-1):
        frame = expandation(frame, max_positions[i][1], max_positions[i][0], side_length, magnification)
        out.write(frame)
        ret, frame = cap.read()
        i = i+1
    out.release()


# `video_0000123_keypoints.json`のようなファイルを
# `123.json`にリネームする`edit.sh`を実行する
def rename_files():
    subprocess.run(['sh', 'edit.sh'])

if __name__ == '__main__':
    '''print('video_path >> ', end="")
    video_path = input()

    print('side_length >> ', end="")
    side_length = int(input())

    print('magnification >> ', end="")
    magnification = float(input())

    #rename_files()
    expand_video(video_path, side_length, magnification)'''

    expand_video('hemmi', 400, 1.5)
