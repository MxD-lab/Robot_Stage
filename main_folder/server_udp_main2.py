# sever
# 送信側
import socket
import pickle
import time
import datetime
import signal
from multiprocessing.spawn import is_forking
from zipimport import zipimporter
from matplotlib.pyplot import axes
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx import stream_readers as sr
import serial
import win_unicode_console
import numpy as np
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
#         print(self.flo1,self.flo2,self.flo3,self.flo4)

class Measure():
    def __init__(self, UPDATE_RATE = 10):
        self.SAMPLE_RATE = 1000 #1秒で取るサンプル数[hz]
        #self.SAMPLE_RATE = 600 #構成処理確認の時だけこっち
        self.UPDATE_RATE = UPDATE_RATE #秒間のデータ更新間隔[hz]c
        self.MAX_TIME = 1000 #最大時間[sec]
        # self.TOCUH_CHECK = 0.05 #接触判定とする値
        # self.EMER_CHECK = 2 #力が加わりすぎたときの判定値[V] 1V≒10N
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai0", terminal_config = TerminalConfiguration.RSE) #ロードセル1ch
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai1", terminal_config = TerminalConfiguration.RSE) #ロードセル2ch
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai2", terminal_config = TerminalConfiguration.RSE) #ロードセル3ch
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai4", terminal_config = TerminalConfiguration.RSE) #触覚センサー1ch
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai5", terminal_config = TerminalConfiguration.RSE) #触覚センサー2ch
        self.task.ai_channels.add_ai_voltage_chan("Dev1/ai6", terminal_config = TerminalConfiguration.RSE) #触覚センサー3ch
        self.task.ai_lowpass_enable = True
        # self.task.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai3")
        self.task.timing.cfg_samp_clk_timing(rate=self.SAMPLE_RATE, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=int(self.SAMPLE_RATE/self.UPDATE_RATE))
        ##しっかりとしたデータ型の定義を忘れずに
        # self.data = np.empty([3,int(self.SAMPLE_RATE/self.UPDATE_RATE)], dtype=float) #ロードセルだけの場合はこちら
        self.data = np.empty([6,int(self.SAMPLE_RATE/self.UPDATE_RATE)], dtype=float)
        #print(self.data.shape)
        # self.contact_flag = 0
        # self.reader = sr.AnalogMultiChannelReader(self.task.in_stream) #ストリーム版

    def update(self): 
        try:
            self.data=np.array(self.task.read(number_of_samples_per_channel=int(self.SAMPLE_RATE/self.UPDATE_RATE), timeout=10.0)) #タイムアウトは秒
            
        except Exception as e:
            print("update_error")
            print(e)


    def get(self):
        return self.data
        # return self.data, self.contact_flag

    def close(self):
        self.task.close()

    def read(self):
        self.task.read()

def to_integer(dt_time):
    return 10000*dt_time.hour + 100*dt_time.minute + dt_time.second


# print("Date and Time in Integer Format:",
#       current_date.year*10000000000 +
#       current_date.month * 100000000 +
#       current_date.day * 1000000 +
#       current_date.hour*10000 +
#       current_date.minute*100 +
#       current_date.second)


dst_ip_addr = '127.0.0.1'
dst_port = 50000


count = 0

if __name__ == '__main__':
    # np.set_printoptions(precision=2)
    mes = Measure(UPDATE_RATE = 1000)
    #mes = Measure(UPDATE_RATE = 600)   #構成処理確認の時だけこっち
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while(True):
    # for __ in range(1):
        try:
            mes.update()
            data = mes.get()
            # dt_now = datetime.datetime.now()
            # int_time = to_integer(dt_now)
            # data_s = np.append(data, int_time)
            # print(data_s)
            msg = pickle.dumps(data)
            server.sendto(msg, (dst_ip_addr, dst_port))


            # if(max_value > 10 or min_value < -10): #これはあってもいいらしい
            #     msg = pickle.dumps("dangerous_super_power!!!")
            #     server.sendto(msg, (dst_ip_addr, dst_port))
            #     print("mesure stopped")
            #     break

            # count += 1
            # time.sleep(0.001)

        except KeyboardInterrupt:
            # a=0
            # msg = pickle.dumps(a)
            # server.sendto(msg, (dst_ip_addr, dst_port))
            break
    
    print("Mesurement is Finish")
    mes.close()
