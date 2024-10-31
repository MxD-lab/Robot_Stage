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
import csv
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
src_ip_addr = '127.0.0.1'
src_port = 50000
buffer_size = 1024


def change_power(raw_data):
    #ロードセルから得られた電圧値をひずみ値にする
    # print(raw_data.shape)
    # print(raw_data)
    # print(raw_data[0])
    # print(raw_data[1])
    # print(raw_data[2])
    # ZERO01 =
    ZERO1 = 0.034#プロット見て手打ちでゼロ校正,chごとに違う
    ZERO2 = 0.195
    ZERO3 = 0.450
    CAL = 500#με
    ZEROCAL01 = 5#V
    ZEROCAL2 = 2.5

    road_mat = np.array([[0.05307, -0.00193, 0.00051], #ロードセルのマトリクス
                [0.00058, 0.05273, 0.00123], 
                [0.00046, 0.00011, 0.06087]], dtype=float)
    
    pow = np.zeros([3,1], dtype=float) #変換後のデータ格納用
#1ch    
    pow[0] = (raw_data[0] - ZERO1) * CAL/ZEROCAL01

#2ch
    pow[1] = (raw_data[1] - ZERO2) * CAL/ZEROCAL01

#3ch
    pow[2] = (raw_data[2] - ZERO3) * CAL/ZEROCAL2

    res = np.dot(road_mat, pow)

    return res


def make_new_file_name(file_top = "dataZ", data_type = ".csv", file_path = "./data/3-14/349/"):
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

#Arduinoと接続、ロボットステージの制御用クラス
class MoterControll():
    ###ロードセルとの接続をコンストラクタで実行
    def __init__(self,port="COM3",baudrate=115200):
        self.serial = serial.Serial(port, baudrate)
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Setup":
                break
        time.sleep(1)
        print("connect")

    ###キャリブレーション呼び出し用メソッドArduinoのCalibration()を呼び出す
    def calibration(self):
        self.serial.write(b"Cal\n")
        print("calbration")
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "fin Calibration":
                break  

    ###moveXYZ()呼び出し用メソッド
    def move_xyz(self,x,y,z,xspeed=1000,yspeed=1000,zspeed=1000):
        com = f"{xspeed},{x},{yspeed},{y},{zspeed},{z}\n"
        self.serial.write(com.encode())
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Done":
                break         

    ###特例moveXYZ()呼び出し用メソッド、触覚センサを定位置に動かすメソッド
    def move_senpos(self):
        #com = b"1000,25000,1000,27000,1000,36000\n" #本来
        com = b"2000,25000,2000,27000,2000,6000\n" #テスト兼デバッグ
        self.serial.write(com)   
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Done":
                break  

    def close(self):
        self.serial.close()

#NiDaqとの接続、ロードセルと触覚センサの情報取得
class DaqMeasure:
    def __init__(self, device_name="Dev1", channels=6, sample_rate=1000, chunk_size=100):
        self.device_name = device_name
        self.channels = channels
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size  # 1回の読み取りで取得するサンプル数

    def measurement(self, filename="daq_data_continuous.csv"):
        # CSVファイルをオープン
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # ヘッダー行の書き込み
            header = [f"Channel {i+1}" for i in range(self.channels)]
            writer.writerow(header)
            
            # NI-DAQmxでアナログ入力タスクを作成
            with nidaqmx.Task() as task:
                # 各チャンネルをシングルエンドモードで設定
                for i in range(self.channels):
                    task.ai_channels.add_ai_voltage_chan(
                        f"{self.device_name}/ai{i}",
                        terminal_config=TerminalConfiguration.RSE
                    )
                
                # サンプリングレートと連続測定モードを設定
                task.timing.cfg_samp_clk_timing(
                    self.sample_rate,
                    sample_mode=AcquisitionType.CONTINUOUS
                )

                print("測定を開始します。Ctrl+Cで終了します。")

                try:
                    while True:
                        # データをチャンクサイズ分取得
                        self.data_chunk = np.array(task.read(number_of_samples_per_channel=self.chunk_size),dtype=float)
                        # データを行ごとにCSVに保存
                        for i in range(self.chunk_size):
                            self.data = [channel_data[i] for channel_data in self.data_chunk]
                            power = change_power(self.data[0:3])
                            for n in range(len(power)):
                                self.data[n] = power[n,0]
                            #print(self.data)
                            writer.writerow(self.data)
                            print(f"z={self.data[2]}")
                except KeyboardInterrupt:
                    print("finish")


    def get(self, channel):
        return self.data[channel]
    

if __name__ == '__main__':
    # motercon = MoterControll()
    # motercon.calibration()
    # motercon.move_senpos()
    # motercon.move_xyz(25000,27000,6000)
    # motercon.close()
    loadread = DaqMeasure()
    loadread.measurement("daq_test.csv")
    while True:
        data = loadread.get(2)
        print(data)
        if(data >= 5):
            break     