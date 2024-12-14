import time
import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx import stream_readers as sr
import serial
import csv
import multiprocessing as mp
from datetime import datetime

def change_power(raw_data,ch1,ch2,ch3):
    #ロードセルから得られた電圧値をひずみ値にする
    CAL = 500#με
    ZEROCAL01 = 5#V
    ZEROCAL2 = 2.5

    road_mat = np.array([[0.05307, -0.00193, 0.00051], #ロードセルのマトリクス
                [0.00058, 0.05273, 0.00123], 
                [0.00046, 0.00011, 0.06087]], dtype=float)
    
    pow = np.zeros([3,1], dtype=float) #変換後のデータ格納用
#1ch    
    pow[0] = (raw_data[0] - ch1) * CAL/ZEROCAL01

#2ch
    pow[1] = (raw_data[1] - ch2) * CAL/ZEROCAL01

#3ch
    pow[2] = (raw_data[2] - ch3) * CAL/ZEROCAL2

    res = np.dot(road_mat, pow)

    return res


#NiDaqとの接続、ロードセルと触覚センサの情報取得
class DaqMeasure(mp.Process):
    def __init__(self, queue, trigger_queue,stop_event,device_name="Dev1", channels=6, sample_rate=1000, chunk_size=100, filename="daq_data_continuous.csv"):
        self.device_name = device_name
        self.channels = channels
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size  # 1回の読み取りで取得するサンプル数
        self.latest_data = None  # 最新の計測データを保持
        self.filename = filename
        self.queue = queue
        self.stop_event = stop_event
        self.trigger_queue = trigger_queue
        super().__init__()


    #計測を行うメソッド呼び出し
    def run(self):
    # CSVファイルをオープン
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # ヘッダー行の書き込み
            header =  ["Timestamp"]+[f"Channel {i+1}" for i in range(self.channels)]+["Trigger"]
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
                    rate = self.sample_rate,
                    samps_per_chan = 2000,
                    sample_mode=AcquisitionType.CONTINUOUS
                )
                # オフセット用 ※非接触スタート前提
                self.data_chunk = np.array(task.read(number_of_samples_per_channel=self.chunk_size),dtype=float)
                averages = np.mean(self.data_chunk, axis=1)
                print("測定を開始")
                try:
                    while not self.stop_event.is_set():
                        # データをチャンクサイズ分取得
                        self.data_chunk = np.array(task.read(number_of_samples_per_channel=self.chunk_size),dtype=float)
                        #時刻の取得（分：秒）秒は小数点第一位まで
                        timestamp = datetime.now().strftime("%M:%S.%f")[:-3]
                        # データを行ごとにCSVに保存
                        for i in range(self.chunk_size):
                            self.data = [channel_data[i] for channel_data in self.data_chunk]
                            power = change_power(self.data[0:3],averages[0],averages[1],averages[2])
                            #queueで共有
                            if self.queue.full():
                                self.queue.get()
                            self.queue.put(power)
                            # Trigger列の値を設定
                            trigger_value = self.trigger_queue.get() if not self.trigger_queue.empty() else 0
                            for n in range(len(power)):
                                self.data[n] = power[n,0]
                            writer.writerow([timestamp]+self.data+[trigger_value])
                        #行の先頭を表示
                        force = f'x={self.data[0]},y={self.data[1]},z={self.data[2]}\n'
                        #print(force)
                        #time.sleep(0.05)                       
                except KeyboardInterrupt:
                    print('計測終了')
                    return

def int_check(val):
    try:
        int(val)
        return True
    except ValueError:
        return False
    
#Arduinoと接続、ロボットステージの制御用クラス
class MotorControll(mp.Process):
    ###ロードセルとの接続をコンストラクタで実行
    def __init__(self,queue,trigger_queue,stop_event,daq_stop_event,port="COM3",baudrate=115200):
        self.queue = queue
        self.port = port
        self.baudrate = baudrate
        self.stop_event = stop_event
        self.daq_stop_event = daq_stop_event
        self.trigger_queue = trigger_queue
        super().__init__()

    ###シリアル通信経由のリセットでsetup()を再実行させる。
    def reset(self,port="COM3",baudrate=115200):
        self.serial = serial.Serial(port, baudrate)
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Setup":
                break
        time.sleep(1)
        print("connect")  
          
    def res_read(self):
        if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
        else:
            response = '0'
        return response
    
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
    
    ##オシロ計測用トリガー信号呼び出し
    def measure_triger(self):
        self.serial.write(b"Tri\n")
        timestamp = datetime.now().microsecond
        if self.trigger_queue.full():
            self.trigger_queue.get()
        self.trigger_queue.put(f"{timestamp}"+'us')
        print("trigger")
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)  
            if response == "tDone":
                break

    ###特例moveXYZ()呼び出し用メソッド、触覚センサを定位置に動かすメソッド
    def move_senpos(self):
        com = b"8000,25000,8000,29000,8000,36000\n" #天板の高さ
        #com = b"8000,25000,8000,29000,8000,35000\n" #ゴム(sozai)の高さ
        #com = b"8000,25000,8000,29000,8000,31000\n" #スポンジ(sozai)の高さ
        self.serial.write(com)
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)  
            if response == "Done":
                break
            # try:
            #     if response.startswith("x="):
            #         xpos = int(response.split("=")[1])
            # #     print(f'xの現在のポジションは{xpos}')
            #     if response.startswith("y="):
            #         ypos = int(response.split("=")[1])
            # #     print(f'xの現在のポジションは{ypos}')
            #     if response.startswith("z="):
            #         zpos = int(response.split("=")[1]) 
            # #     print(f'xの現在のポジションは{zpos}'
            # except (ValueError,AttributeError) as e:
            #     print(e)
            #     continue    

    
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
            # if response.split("=")[0]=="x":
            #     xpos = int(response.split("=")[1])
            # if response.split("=")[0]=="y":
            #     ypos = int(response.split("=")[1])
            # if response.split("=")[0]=="z":
            #     zpos = int(response.split("=")[1]) 
        #return xpos,ypos,zpos
    
    ###力を一定に保つための関数ループ内で使用、xpos,ypos,zposが座標,fがキープする力、powerがniからの取得データ
    def keep_forceZ(self,xpos,ypos,zpos,power,f):
        if power[2][0] <= f:
            zpos = zpos +1
            self.move_xyz(xpos,ypos,zpos,0,0,1)
        else:
            time.sleep(1)
        return zpos

    def keep_forceX(self,xpos,ypos,zpos,power,f):
        if power[0][0] <= f:
            xpos = xpos -1
            self.move_xyz(xpos,ypos,zpos,1,0,0)
        else:
            time.sleep(1)
        return xpos

    def keep_forceY(self,xpos,ypos,zpos,power,f):
        if power[1][0] <= f:
            ypos = ypos -1
            self.move_xyz(xpos,ypos,zpos,0,1,0)
        else:
            time.sleep(1)
        return ypos   
         
    ####moveToForce~()呼び出し用メソッド
    def moveToSpeed(self,xspeed=0,yspeed=0,zspeed=0):
       com = f"{xspeed},{yspeed},{zspeed}\n"
       self.serial.write(com.encode())
       #self.serial.flush()
       while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("move cmd Arduino:", response)
            if response == "moving":
                break
       
    ######使用しない   
    def move_stop(self):
        self.serial.write(b"STOP\n")
        print('Stop')
        #self.serial.flush()
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Stop cmd Arduino:res:", response)
            if response == "Done":
                break 

    def close(self):
        self.serial.close()

    #####niでの計測をするプロセスを立てる
    def daq_start(self):
        self.daq_measure = DaqMeasure(self.queue,self.trigger_queue,self.daq_stop_event,chunk_size=20)
        self.daq_measure.start()
        print('Daq 計測開始')

    ######動作記述########
    def run(self):
        #####以下サンプル########################################
        #####シリアルでArduinoと通信開始,キャリブレーションを行ってセンサ近くまで天板を動かす。座標はx=25000,y=27000,z=36000
        #####センサポジションを動かしたのちNiDaqでの計測開始
        #####while内でループするためstateで状態遷移をする
        #####self.queue.get()でNiDaqからのデータ取得、power[0][0]=x,power[1][0]=y,power[2][0]=z
        #####
        #####～～～～～～～～本サンプルの動作手順～～～～～～～～～～
        #####荷重方向に3Nかかるまで押す
        #####何秒間かキープ
        #####荷重方向に5Nかかるまで押す
        #####何秒間かキープ
        #####3Nに戻す
        #####何秒間かx方向に動かす
        #####-y方向に動かす。(x,yはマイナス方向に動かすとロードセルの力がプラス方向になる)
        #####x,-y方向のななめに動かす。
        #####もとのポジションに動かす。
        #####終了
        #####～～～～～～～～～～～～～～～～～～～～～～～～～～～～～
        #####
        #####基本的に制御はmove_xyz()でおこない、荷重方向にキープしたい場合はkeep_forceZ()を呼ぶ
        #####range(x)のxで長い時間やるのか短い時間やるのかを決める。
        #状態管理用
        state = 0
        try:
            self.serial = serial.Serial(self.port,self.baudrate)

            while True:
                if self.serial.in_waiting > 0:
                    response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    print("Arduino:", response)
                    if response == "Setup":
                        break
                time.sleep(0.1)   
            print("connect")
 
        
            self.calibration()
            self.move_senpos()

            ## daq計測開始　オフセットの関係で接触してない地点で開始すること
            time.sleep(0.5)
            self.daq_start()
            xpos = 25000
            ypos = 29000
            zpos = 36000 #天板
            #zpos = 35000 #ゴム
            #zpos = 31000 #スポンジ
            while not self.stop_event.is_set():
                if not self.queue.empty():
                    power = self.queue.get()
                    res = self.res_read()
                    print(f'receive power = {power},状態は{state},arduinoの応答は{res}')
                    if state == 0:
                        zpos = zpos + 1
                        self.move_xyz(xpos,ypos,zpos,0,0,20)
                        if power[2][0] >= 1:
                            state += 1
                    if state == 1:
                        self.measure_triger()
                        ypos = ypos + 1000
                        self.move_xyz(xpos,ypos,zpos,0,2000,0)
                        ypos = ypos - 1000
                        self.move_xyz(xpos,ypos,zpos,0,2000,0) 
                                                
                        #およそ1cm移動の往復を2回                                                  
                        state += 1
                    if state == 2:
                        self.move_xyz(25000,29000,36000,50,50,50) #天板
                        #self.move_xyz(25000,29000,35000,50,50,50) #ゴム
                        #self.move_xyz(25000,29000,31000,50,50,50) #スポンジ
                        state += 1
                    if state == 3:
                        #次回のキャリブレーションを短くするための移動
                        self.move_xyz(3000,3000,3000,2000,2000,2000)
                        state += 1
                    if state == 4:
                        break
                    # elif state == 2:
                    #     for i in range(10):
                    #         ####for文ないではpowerが更新されないので再取得
                    #         power = self.queue.get()
                    #         zpos = self.keep_forceZ(xpos,ypos,zpos,power,3)
                    #     state += 1                    
                    # elif state == 3:
                    #     if power[2][0] <= 5:
                    #         zpos = zpos +1
                    #         self.move_xyz(xpos,ypos,zpos,0,0,10)
                    #     else:
                    #         state +=1
                    # elif state == 4:
                    #     for i in range(10):
                    #         power = self.queue.get()
                    #         zpos = self.keep_forceZ(xpos,ypos,zpos,power,5)
                    #     state += 1
                    # elif state == 5:
                    #     if power[2][0] >= 3:
                    #         zpos = zpos -1
                    #         self.move_xyz(xpos,ypos,zpos,0,0,10)
                    #     else:
                    #         state += 1
                    # elif state == 6:
                    #     # if power[0][0] <= 2:
                    #     for i in range(100):
                    #         xpos = xpos -1
                    #         self.move_xyz(xpos,ypos,zpos,10,0,0)
                    #     # else:
                    #         #state +=1
                    #     state += 1
                    # elif state == 7:
                    #     for i in range(50):
                    #         ypos = ypos + 1
                    #         self.move_xyz(xpos,ypos,zpos,0,10,0)
                    #     state += 1
                    # elif state ==8:
                    #     for i in range(200):
                    #         ypos = ypos + 1
                    #         xpos = xpos - 1
                    #         self.move_xyz(xpos,ypos,zpos,10,10,0)
                    #     state +=1
                    # elif state == 9:
                    #     self.move_xyz(25000,27000,36000,20,20,20)
                    #     state +=1
                    # elif state == 10:
                    #     break  
            print('試行終了')
        except KeyboardInterrupt:
            #self.move_senpos()
            self.close()
            print('通信終了')
        finally:
            if self.daq_measure:
                self.daq_stop_event.set()
                self.daq_measure.join()
                print('Daq計測終了')
            print('arduino 終了')



if __name__ == '__main__':

    queue = mp.Queue(3)
    trigger_queue = mp.Queue(3)
    stop_event = mp.Event()
    daq_stop_event = mp.Event()

    motor = MotorControll(queue,trigger_queue,stop_event,daq_stop_event)

    try:
        motor.start()
           
    except KeyboardInterrupt:     
        stop_event.set()
        daq_stop_event.set()
        print("Program interrupted")
    finally:
        motor.join()
        print('fin')       
