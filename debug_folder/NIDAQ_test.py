"""
2022/07/10 記入者：船橋佑｜NIDAQのコードを理解するためのテストプログラムを作成。
"""

import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx import stream_readers as sr
import numpy as np

class Measure():
    def __init__(self, UPDATE_RATE = 10):
        self.SAMPLE_RATE = 2000 #1秒で取るサンプル数[hz]
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



if __name__ == '__main__':
    mes = Measure(UPDATE_RATE = 2000)
    while(True):
        try:
            mes.update()
            data = mes.get()
            print(data[2])

        except KeyboardInterrupt:
            break

    print("Mesurement is Finish")
    mes.close()