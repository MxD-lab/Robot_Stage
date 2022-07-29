# client
# 受信側
# 先にこっち（受信側）を実行してから送信側のコードを実行します．




import socket
import serial
from serial.tools import list_ports
import pickle
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


def make_new_file_name(file_top = "gomi", data_type = ".csv", file_path = "./gomi/"):
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

def mesurement(lock):
    for __ in range(10):

        print("unchi")
    # ser = UseSerial("/dev/cu.usbmodem1101") #megaの方 モーター用

    # ser.send("cariv_start"+";") #まずはXのキャリブレーションをする
    # while(True):
    #     str_buf = ser.readline().strip().decode('utf-8')
    #     if str_buf == "cariv_end":
    #         break

    # ser.close()

class UseSerial():
    def __init__(self, port_name):
        self.ser = serial.Serial(port_name,115200,timeout=1)

    def send(self, char):
        flag=bytes(char,'utf-8')
        self.ser.write(flag)

    def write(self, byte):
        self.ser.write(byte)

    def close(self):
        self.ser.close()     

    def readline(self):
        data=self.ser.readline()
        return data 

    def inWaiting(self):
        mes=self.ser.inWaiting()
        return mes
    
    def reset_input_buffer(self):
        self.ser.reset_input_buffer()


src_ip_addr = '127.0.0.1'
src_port = 50000
buffer_size = 1024
ZERO1 = -0.16#プロット見て手打ちでゼロ校正,chごとに違う
ZERO2 = 0.06
ZERO3 = 0.15
CAL = 500#με
ZEROCAL01 = 5#V
ZEROCAL2 = 2.5
CARIV_SPEED = 1200
CHECK = "s"

road_mat = np.array([[0.05307, -0.00193, 0.00051], #ロードセルのマトリクス
            [0.00058, 0.05273, 0.00123], 
            [0.00046, 0.00011, 0.06087]], dtype=float)

if __name__ == '__main__':
    danger_flag = 0 #過負荷のフラグ

    np.set_printoptions(precision=2)
    lock = Lock()


    #シリアル通信開始、まずはモーターの位置を調整するキャリブレーションをする
    ser = UseSerial("COM3") #megaの方 モーター用
    time.sleep(1)
    #print(ser)

    #モーターの動作開始
    ser.send("cariv_start;") #まずはXのキャリブレーションをする
    # print("モーターの速度は:"+str(CARIV_SPEED)+"です")
    # time.sleep(2.0)
    
    while(True):
        if ser.inWaiting():
            str_buf = ser.readline().strip().decode('utf-8')
            if str_buf == 'cariv_end':
                print("carivration end")
                break
    # ser.close()
    # print("-----")
    #計測用のモーターの動作開始
    morter_drive = Thread(target=mesurement, args=(lock,))
    

    # ni2baffer_fase.setDaemon(True) #デーモン化 <-これがだめ

    morter_drive.start()

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((src_ip_addr,src_port))
    f = open(make_new_file_name() + ".csv",'ab')
    
    count = 0
    start_time = time.perf_counter()

    msg, addr = server.recvfrom(buffer_size)
    first_data = pickle.loads(msg)# バイナリデータを復元
    f_road, f_sens = np.split(first_data, 2)
    f_road = change_power(f_road)

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

            road_max = np.max(road_sell_data)
            road_min = np.min(road_sell_data)

            if(road_max > 10 or road_min < -10):
                print("dangerous!!")
                danger_flag = 1
                # break
            else:
                danger_flag = 0 

            full_data = np.concatenate([road_sell_data, sens])

            np.savetxt(f, full_data.T ,fmt="%0.6f", delimiter=",")


            # print(road_sell_data)
            # print(type(data))
            # count += 1
            # if(data==0):
            #     break
            # else:
            #     print(data)
            # print(msg)
            # print(data)
            #print(addr)
            # data.print_data()
            # print(time.time())

        except KeyboardInterrupt:
            break
    f.close()
    end_time = time.perf_counter()

    morter_drive.join()
    # print("data_num: ", count)
    # print(end_time - start_time)