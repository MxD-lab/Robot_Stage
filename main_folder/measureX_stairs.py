# client
# 受信側
# あとからこっち（受信側）を実行する。先に送信側(server_udp_main2.py)のコードを実行します．




import socket
import pickle
import threading
import time
import numpy as np
from multiprocessing.spawn import is_forking
from zipimport import zipimporter
from matplotlib.pyplot import axes, axis
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx import stream_readers as sr
import serial
import win_unicode_console
import os
import re
import sys
import traceback
from threading import Thread, Lock
from queue import Queue
import signal
from collections import deque
import itertools

'''
2022/06/09 プロセス間でのUDP通信できることを確認（ネットから拾ったコード動かしただけ）
'''


# 通信したいオブジェクトの定義
# class xyz_data:
#     def __init__(self, flo1, flo2, flo3, flo4):
#         self.flo1 = flo1
#         self.flo2 = flo2
#         self.flo3 = flo3
#         self.flo4 = flo4
#         # self.flo5 = flo5
#         # self.flo6 = flo6
#         # self.flo7 = flo7
#         # self.flo8 = flo8

#     def print_data(self):
#         print(self.flo1,self.flo2,self.flo3,self.flo4,self.flo5,self.flo6,self.flo7,self.flo8)

def change_power(raw_data):
    #ロードセルから得られた電圧値をひずみ値にする
    # print(raw_data.shape)
    # print(raw_data)
    # print(raw_data[0])
    # print(raw_data[1])
    # print(raw_data[2])
    # ZERO01 =
    pow = np.zeros([3,1], dtype=float) #変換後のデータ格納用
#1ch    
    pow[0] = (raw_data[0] - ZERO1) * CAL/ZEROCAL01

#2ch
    pow[1] = (raw_data[1] - ZERO2) * CAL/ZEROCAL01

#3ch
    pow[2] = (raw_data[2] - ZERO3) * CAL/ZEROCAL2

    
    res = np.dot(road_mat, pow)

    return res


def make_new_file_name(file_top = "dataX", data_type = ".csv", file_path = "./data/11-16/"):
    num_pat = r'([+-]?[0-9]+\.?[0-9]*)'
    numpatter = re.compile(num_pat)
    namepatter = re.compile(file_top)
    tmp= 0
    # easy_name = "pressure_and_speed_data/gomi/"
    # file_path =file_path+easy_name

    os.makedirs(file_path,exist_ok=True)
    

    for filename in os.listdir(file_path):
        name, path  = os.path.splitext(filename)
        if path == data_type:
            num_match = numpatter.search(name)
            name_match = namepatter.match(name)
            if num_match and name_match != None:
                if tmp < int(num_match.group()):
                    
                    tmp = int(num_match.group())

    return file_path+file_top +"_"+ str(tmp+1)#+data_type


def morter_move():
    global start_cul_flag
    global end_flag
    global road_Z

    # ser = serial.Serial("COM3", 115200) 
    time.sleep(1)
 
    ser.write(bytes("2;",'utf-8'))
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '2':
                    print("carivration end")
                    break

            elif road_Z >= 5:
                ser.write(bytes("stop;",'utf-8'))
                print("em end")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break

    #ここでキャリブレーションは終了
    if end_flag == -1:
        end_flag = 0 #計測開始
    
    
    time.sleep(1)
    

    #ここからZ軸を降ろして指定の圧力をかける
    ser.write(bytes("3;",'utf-8'))
    print("move_z_start")
    while(True):
        print(road_Z)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                print('foge')
                if str_buf == '3':
                    print("z_end")
                    break

            #指定の圧力
            elif 1.2 >= road_Z >= 1.0:
                ser.write(bytes("8;", 'utf-8'))
                print("setZ")
                # break


            #過剰な圧力が加わったら            
            elif road_Z >= 5: 
                ser.write(bytes("9;",'utf-8'))
                print("emfin")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break
    
    
    time.sleep(1)
    #ここからX軸をうごかす
    ser.write(bytes("4;",'utf-8'))
    while(True):
        print(road_X)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '4':
                    print("x_end")
                    break

            elif 1.05 < road_Z:
                ser.write(bytes("Z-;", 'utf-8'))
                # print("-")

            elif 1.05 >= road_Z >= 0.95:
                ser.write(bytes("stay;", 'utf-8'))

            elif 0.95 > road_Z:
                ser.write(bytes("Z+;", 'utf-8'))
                # print("+")

            elif road_Z > 5: 
                ser.write(bytes("stop;",'utf-8'))
                print("emfin2")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break

    print("x軸に指定の圧力がかかってます")
    
    time.sleep(10)

    print("あがるよ")
    ser.write(bytes("7;",'utf-8'))
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '7':
                    print("next")
                    break

            elif road_Z >= 5:
                ser.write(bytes("stop;",'utf-8'))
                print("em end")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break
 
    time.sleep(1)

    #二回目
    #ここからZ軸を降ろして指定の圧力をかける
    ser.write(bytes("3;",'utf-8'))
    print("move_z_start")
    while(True):
        print(road_Z)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                print('foge')
                if str_buf == '3':
                    print("z_end")
                    break

            #指定の圧力
            elif 3.2 >= road_Z >= 3.0:
                ser.write(bytes("8;", 'utf-8'))
                print("setZ")
                # break


            #過剰な圧力が加わったら            
            elif road_Z >= 5: 
                ser.write(bytes("9;",'utf-8'))
                print("emfin")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break
    
    
    time.sleep(1)
    #ここからX軸をうごかす
    ser.write(bytes("4;",'utf-8'))
    while(True):
        print(road_X)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '4':
                    print("x_end")
                    break

            elif 3.05 < road_Z:
                ser.write(bytes("Z-;", 'utf-8'))
                # print("-")

            elif 3.05 >= road_Z >= 2.95:
                ser.write(bytes("stay;", 'utf-8'))

            elif 2.95 > road_Z:
                ser.write(bytes("Z+;", 'utf-8'))
                # print("+")

            elif road_Z > 5: 
                ser.write(bytes("stop;",'utf-8'))
                print("emfin2")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break
    
    print("x軸に指定の圧力がかかってます")

    time.sleep(10)

    ser.write(bytes("7;",'utf-8'))
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '7':
                    print("next")
                    break

            elif road_Z >= 5:
                ser.write(bytes("stop;",'utf-8'))
                print("em end")
                end_flag = 1
                break

        except KeyboardInterrupt:
            break
    
    time.sleep(1)

    #三回目
    #ここからZ軸を降ろして指定の圧力をかける
    ser.write(bytes("3;",'utf-8'))
    print("move_z_start")
    while(True):
        print(road_Z)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                print('foge')
                if str_buf == '3':
                    print("z_end")
                    break

            #指定の圧力
            elif 5.2 >= road_Z >= 5.0:
                ser.write(bytes("8;", 'utf-8'))
                print("setZ")
                # break


            # #過剰な圧力が加わったら            
            # elif road_Z >= 5: 
            #     ser.write(bytes("9;",'utf-8'))
            #     print("emfin")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break
    
    
    time.sleep(1)
    #ここからX軸をうごかす
    ser.write(bytes("4;",'utf-8'))
    while(True):
        print(road_X)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '4':
                    print("x_end")
                    break

            elif 5.05 < road_Z:
                ser.write(bytes("Z-;", 'utf-8'))
                # print("-")

            elif 5.05 >= road_Z >= 4.95:
                ser.write(bytes("stay;", 'utf-8'))

            elif 4.95 > road_Z:
                ser.write(bytes("Z+;", 'utf-8'))
                # print("+")

            # elif road_Z > 5: 
            #     ser.write(bytes("stop;",'utf-8'))
            #     print("emfin2")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break
    print("x軸に指定の圧力がかかってます")

    time.sleep(10)

    ser.write(bytes("7;",'utf-8'))
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '7':
                    print("next")
                    break

            # elif road_Z >= 5:
            #     ser.write(bytes("stop;",'utf-8'))
            #     print("em end")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break

    time.sleep(1)

    #四回目
    #ここからZ軸を降ろして指定の圧力をかける
    ser.write(bytes("3;",'utf-8'))
    print("move_z_start")
    while(True):
        print(road_Z)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                print('foge')
                if str_buf == '3':
                    print("z_end")
                    break

            #指定の圧力
            elif 7.2 >= road_Z >= 7.0:
                ser.write(bytes("8;", 'utf-8'))
                print("setZ")
                # break


            # #過剰な圧力が加わったら            
            # elif road_Z >= 5: 
            #     ser.write(bytes("9;",'utf-8'))
            #     print("emfin")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break
    
    
    time.sleep(1)
    #ここからX軸をうごかす
    ser.write(bytes("4;",'utf-8'))
    while(True):
        print(road_X)
        try:
            if(end_flag==1):
                break

            elif ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '4':
                    print("x_end")
                    break

            elif 7.05 < road_Z:
                ser.write(bytes("Z-;", 'utf-8'))
                # print("-")

            elif 7.05 >= road_Z >= 6.95:
                ser.write(bytes("stay;", 'utf-8'))

            elif 6.95 > road_Z:
                ser.write(bytes("Z+;", 'utf-8'))
                # print("+")

            # elif road_Z > 5: 
            #     ser.write(bytes("stop;",'utf-8'))
            #     print("emfin2")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break

    print("x軸に指定の圧力がかかってます")

    time.sleep(10)

    ser.write(bytes("7;",'utf-8'))
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                if str_buf == '7':
                    print("next")
                    break

            # elif road_Z >= 5:
            #     ser.write(bytes("stop;",'utf-8'))
            #     print("em end")
            #     end_flag = 1
            #     break

        except KeyboardInterrupt:
            break

    time.sleep(1)

    # #五回目
    # #ここからZ軸を降ろして指定の圧力をかける
    # ser.write(bytes("3;",'utf-8'))
    # print("move_z_start")
    # while(True):
    #     print(road_Z)
    #     try:
    #         if(end_flag==1):
    #             break

    #         elif ser.inWaiting():
    #             str_buf = ser.readline().strip().decode('utf-8')
    #             print('foge')
    #             if str_buf == '3':
    #                 print("z_end")
    #                 break

    #         #指定の圧力
    #         elif 9.2 >= road_Z >= 9.0:
    #             ser.write(bytes("8;", 'utf-8'))
    #             print("setZ")
    #             # break


    #         # #過剰な圧力が加わったら            
    #         # elif road_Z >= 5: 
    #         #     ser.write(bytes("9;",'utf-8'))
    #         #     print("emfin")
    #         #     end_flag = 1
    #         #     break

    #     except KeyboardInterrupt:
    #         break
    
    
    # time.sleep(1)
    # #ここからX軸をうごかす
    # ser.write(bytes("4;",'utf-8'))
    # while(True):
    #     print(road_X)
    #     try:
    #         if(end_flag==1):
    #             break

    #         elif ser.inWaiting():
    #             str_buf = ser.readline().strip().decode('utf-8')
    #             if str_buf == '4':
    #                 print("x_end")
    #                 break

    #         elif 9.05 < road_Z:
    #             ser.write(bytes("Z-;", 'utf-8'))
    #             # print("-")

    #         elif 9.05 >= road_Z >= 8.95:
    #             ser.write(bytes("stay;", 'utf-8'))

    #         elif 8.95 > road_Z:
    #             ser.write(bytes("Z+;", 'utf-8'))
    #             # print("+")

    #         # elif road_Z > 5: 
    #         #     ser.write(bytes("stop;",'utf-8'))
    #         #     print("emfin2")
    #         #     end_flag = 1
    #         #     break

    #     except KeyboardInterrupt:
    #         break
    
    # print("x軸に指定の圧力がかかってます")

    # time.sleep(10)

    # ser.write(bytes("7;",'utf-8'))
    # while(True):
    #     try:
    #         if ser.inWaiting():
    #             str_buf = ser.readline().strip().decode('utf-8')
    #             if str_buf == '7':
    #                 print("next")
    #                 break

    #         # elif road_Z >= 5:
    #         #     ser.write(bytes("stop;",'utf-8'))
    #         #     print("em end")
    #         #     end_flag = 1
    #         #     break

    #     except KeyboardInterrupt:
    #         break

    # time.sleep(1)
    ser.close()
    end_flag = 1
    
    # ser.write(bytes("cu_end;",'utf-8'))
    


    

src_ip_addr = '127.0.0.1'
src_port = 50000
buffer_size = 1024
ZERO1 = -0.16#プロット見て手打ちでゼロ校正,chごとに違う
ZERO2 = 0.06
ZERO3 = 0.15
CAL = 500#με
ZEROCAL01 = 5#V
ZEROCAL2 = 2.5

road_mat = np.array([[0.05307, -0.00193, 0.00051], #ロードセルのマトリクス
            [0.00058, 0.05273, 0.00123], 
            [0.00046, 0.00011, 0.06087]], dtype=float)

if __name__ == '__main__':
    global road_Z
    global road_X
    global road_Y
    global start_cul_flag
    global end_flag #-1がキャリブレーションモード、0が計測モード、1が終了モード

    np.set_printoptions(precision=2)
    # server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # server.bind((src_ip_addr,src_port))
    morter = threading.Thread(target=morter_move)
    f = open(make_new_file_name() + ".csv",'ab')
    
    count = 0
    start_time = time.perf_counter()
    
    ser = serial.Serial("COM3", 115200) 
    time.sleep(1)
    ser.write(bytes("1;",'utf-8'))
    # print("one")
    while(True):
        try:
            if ser.inWaiting():
                str_buf = ser.readline().strip().decode('utf-8')
                # print("koko")
                if str_buf == '1':
                    break

        except KeyboardInterrupt:
            break
    time.sleep(1)
    
    # print("owa")
    
    
    # start_cul_flag = False

    # while start_cul_flag == False:
    #     print("mada")

    end_flag = -1
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((src_ip_addr,src_port))

    
    msg, addr = server.recvfrom(buffer_size)
    # time.sleep(5)
    for i in range(100):
        f_data = pickle.loads(msg)# バイナリデータを復元
        if i == 0:
            first_data = f_data

        else:
            first_data = first_data + f_data

    first_data = first_data / 100
    f_road, f_sens = np.split(first_data, 2)
    f_road = change_power(f_road)
    morter.start()


    # for __ in range(1):
    while True:
        try:
            msg, addr = server.recvfrom(buffer_size)
            # print(msg)
            data = pickle.loads(msg)# バイナリデータを復元
            road, sens = np.split(data, 2)

            road_sell_data = change_power(road)
            road_sell_data = road_sell_data - f_road
            sens = sens - f_sens

            # road_max = np.max(road_sell_data)
            # road_min = np.min(road_sell_data)

            # print(road_sell_data.T)

            road_Z = road_sell_data[2]
            # print(road_Z)
            road_X = road_sell_data[0]
            road_Y = road_sell_data[1]

            # if(road_max > 10 or road_min < -10):
            # if(road_Z > 10):
            #     print("dangerous!!")
            #     break
            if(end_flag == 1):
                print("fin!!")
                break

            full_data = np.concatenate([road_sell_data, sens])

            if(end_flag == 0):
                # print("saving...")
                np.savetxt(f, full_data.T ,fmt="%0.6f", delimiter=",")


        except KeyboardInterrupt:
            break
    f.close()
    end_time = time.perf_counter()