# -*- coding: utf-8 -*-
import glob
import json
import math
import subprocess

import cv2


def expandation(img, y, x, padding, magnification):
    '''
    (x,y)を中心に1辺paddingの正方形を抽出し
    magnification倍に拡大したものを上書きして描画したデータを返す
    '''
    # img = cv2.imread(img_path)
    h, w = img.shape[:2]
    padding //= 2
    x = int(x)
    y = int(y)

    if x == 0 and y == 0:
        'たぶんトラッキング失敗してる'
        return img

    x_lb = int(max(x-padding, 0))
    x_ub = int(min(x+padding, w-1))
    y_lb = int(max(y-padding, 0))
    y_ub = int(min(y+padding, h-1))

    selected_img = img[y_lb:y_ub, x_lb:x_ub]

    #expanded_img = cv2.resize(selected_img, (int((y_ub-y_lb)*magnification), int((x_ub-x_lb)*magnification)))
    expanded_img = cv2.resize(selected_img, dsize=None ,fx=magnification, fy=magnification)
    padding = int(padding*magnification)

    '''
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
    '''

    e_h, e_w = expanded_img.shape[:2]
    #print(e_w, e_h)

    X = int(x+padding)
    Y = int(y+padding)
    #print(X,Y)

    ex_lb = int(min(0,math.fabs(X-e_w)))
    ey_lb = int(min(0,math.fabs(Y-e_h)))

    ex_ub = int(min(e_w, e_w-(X-w)))
    ey_ub = int(min(e_h, e_h-(Y-h)))

    '------'

    x_lb = max(0,int(x-padding))
    y_lb = max(0, int(y-padding))

    x_ub = int(min(w, X))
    y_ub = int(min(h, Y))
    #print(ex_lb,ex_ub, ey_lb, ey_ub)
    #print(x_lb, x_ub, y_lb, y_ub)

    try:
        'ちょっとわかんない'
        img[y_lb:y_lb+ey_ub-ey_lb, x_lb:x_ub] = expanded_img[ey_lb:ey_ub, ex_lb:ex_ub]
    except Exception as e:
        print(e)
        print('fucked frame')
        cv2.imwrite('./y{}_x{}.png'.format(y, x), expanded_img)
        with open('fuck.txt', 'a') as f:
            f.write(f'x{x} y{y} X{X} Y{Y} y_ub{y_ub} size {y_ub - y_lb} , {ey_ub-ey_lb}\n')
    return img

def get_distance(positions, id, label):
    '''
    positions配列のlabelという名前の要素について
    id+1番目とid番目の距離を返す
    '''
    return math.sqrt(math.fabs((positions[id+1].get(label)[1] - positions[id].get(label)[1])**2 \
    - (positions[id+1].get(label)[0] - positions[id].get(label)[0])**2))


def expand_video(video_path, side_length, magnification):
    '''
    video_pathが指すvideoから
    1辺side_lengthの正方形を選択し
    magnification倍したvideoを書き出す
    前処理として動画のファイル名と同名のフォルダに
    openposeでjson形式に書き出した連番データを入れておく
    '''
    positions = []

    dir_path = video_path.split('.')[0]
    frame_length = len(glob.glob(dir_path+"/*.json"))

    for i in range(frame_length):
        tmp = None
        with open('{}/{}.json'.format(dir_path, i), 'r') as f:
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
        fuck.append((max_distance,positions[i].get(max_distance),positions[i]))
        max_positions.append(positions[i].get(max_distance))

    with open('max_parts.txt', 'w') as f:
        for i in fuck:
            f.write('{}\n'.format(i))
        for i in max_positions:
            f.write('x{}, y{}\n'.format(i[0], i[1]))

    cap = cv2.VideoCapture(video_path)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    ret, frame = cap.read()
    i = 0
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter(f'{dir_path}_out.mp4', fourcc, fps, (W, H))

    for i in range(frame_length-1):
        frame = expandation(frame, max_positions[i][1], max_positions[i][0], side_length, magnification)
        out.write(frame)
        ret, frame = cap.read()
        i = i+1
    out.release()

if __name__ == '__main__':
    '''
    video_path = input('video_path >> ')

    side_length = int(input('side_length >> '))

    magnification = float(input('magnification >> '))

    expand_video(video_path, side_length, magnification)
    '''

    expand_video('video.mp4', 200, 1.5)
