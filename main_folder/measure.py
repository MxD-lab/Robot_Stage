import time
import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx import stream_readers as sr
import serial
import csv
from threading import Thread, Event
'''
2022/06/09 プロセス間でのUDP通信できることを確認（ネットから拾ったコード動かしただけ）
'''


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


#Arduinoと接続、ロボットステージの制御用クラス
class MoterControll():
    ###ロードセルとの接続をコンストラクタで実行
    def __init__(self,port="COM3",baudrate=115200):
        self.serial = serial.Serial(port,baudrate)
        #self.serial.setDTR(False) 現状効果なし
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Setup":
                break
        time.sleep(1)
        print("connect")

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

    ###特例moveXYZ()呼び出し用メソッド、触覚センサを定位置に動かすメソッド
    def move_senpos(self):
        #com = b"2000,25000,2000,27000,2000,36000\n" #本来
        com = b"2000,5000,2000,4000,2000,8000\n" #テスト用
        self.serial.write(com)   
        while True:
          if self.serial.in_waiting > 0:
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            print("Arduino:", response)
            if response == "Done":
                break  

    ###moveXYZ()呼び出し用メソッド
    def move_xyz(self,x,y,z,xspeed=1000,yspeed=1000,zspeed=1000):
        com = f"{xspeed},{x},{yspeed},{y},{zspeed},{z}\n"
        self.serial.write(com.encode())
        #self.serial.flush()
    
    ####moveToForce~()呼び出し用メソッド
    def moveToForce(self,xspeed=0,yspeed=0,zspeed=0):
       com = f"x={xspeed},y={yspeed},z={zspeed}"
       self.serial.write(com.encode())
       #self.serial.flush()
       
    def move_stop(self):
        self.serial.write(b"STOP\n")
        #self.serial.flush()

    def close(self):
        self.serial.close()

#NiDaqとの接続、ロードセルと触覚センサの情報取得
class DaqMeasure(MoterControll):
    def __init__(self, device_name="Dev1", channels=6, sample_rate=1000, chunk_size=50):
        self.device_name = device_name
        self.channels = channels
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size  # 1回の読み取りで取得するサンプル数
        self.latest_data = None  # 最新の計測データを保持
        #self.running = Event()  # 計測の開始/停止を管理するイベント        
        super().__init__()

    #計測を行うメソッド呼び出し
    def measurement(self, filename="daq_data_continuous.csv"):
        def measure_vi():
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

                    print("測定を開始")

                    while self.running.is_set():
                        # データをチャンクサイズ分取得
                        self.data_chunk = np.array(task.read(number_of_samples_per_channel=self.chunk_size),dtype=float)
                        # データを行ごとにCSVに保存
                        for i in range(self.chunk_size):
                            self.data = [channel_data[i] for channel_data in self.data_chunk]
                            power = change_power(self.data[0:3])
                            self.latest_data = power
                            #self.dataのロードセル部分を力変換かけたものに置き換え
                            for n in range(len(power)):
                                self.data[n] = power[n,0]
                            writer.writerow(self.data)
                        #行の先頭を表示
                        force = f'x={self.data[0]},y={self.data[1]},z={self.data[2]}\n'
                        print(force)                       
        #self.running.set()
        Thread(target=measure_vi, daemon=True).start()

    def get_latest_data(self):
        #print(self.latest_data)
        return self.latest_data

    # def stop_measurement(self):
    #     self.running.clear()




if __name__ == '__main__':
    ##この2つをどう動かすかスレッドにするかソケット通信にするか
    loadread = DaqMeasure()
    loadread.calibration()
    loadread.move_senpos()
    #################################################################################
    ####以下計測動作サンプル###########################################################
        # loadread.moveToForce(xspeed,yspeed,zspeed)
        # while True:
        #     if latest_data is not None:
        #         ?_force = latest_data[?][0]  #z方向の力を取得
        #         if ?_force >= N:
        #             print(f"Set force detected: ?={?_force}")
        #             loadread.move_stop()
        #             break
        #         else:
        #             print(f"Force within range: ?={?_force}")
        #     time.sleep(0.5)
    ####上記を一つのシーケンスで順に動作していく運用

    ##~~サンプル動作~~
    ####Zを3N下げその後少しまって違う速度で5Nまで下げる
    ####その後3Nまであげる
    ####x方向に動かした後、y方向に動かす。
    ####どちらも動いた後高さをそのままにもとの位置に斜めにもどす。
    ####最後に開始位置にもどす
    try:
        # 計測スレッドを開始
        loadread.measurement("daq_data_test.csv")
        #z軸方向動かす。
        loadread.moveToForce(0,0,-20)
        # メインスレッドでArduinoを制御
        while True:
            latest_data = loadread.get_latest_data()
            if latest_data is not None:
                z_force = latest_data[2][0]  #z方向の力を取得
                print(type(z_force))
                if z_force >= 3:
                    print(f"Set force detected: z={z_force}")
                    loadread.move_stop()
                    break
                else:
                    print(f"Force within range: z={z_force}")
            time.sleep(0.5)
        time.sleep(1)

        loadread.moveToForce(0,0,-10)
        while True:
            latest_data = loadread.get_latest_data()
            if latest_data is not None:
                z_force = latest_data[2][0]  #z方向の力を取得
                if z_force >= 5:
                    print(f"Set force detected: z={z_force}")
                    loadread.move_stop()
                    break
                else:
                    print(f"Force: z={z_force}")
            time.sleep(0.5)

        loadread.moveToForce(0,0,10)
        while True:
            loadread.res_read()
            if loadread.res_read() != '0':
                zpos = int(loadread.res_read())
            latest_data = loadread.get_latest_data()
            if latest_data is not None:
                z_force = latest_data[2][0]  #z方向の力を取得
                if z_force <= 3:
                    print(f"Set force detected: z={z_force}")
                    loadread.move_stop()
                    break
                else:
                    print(f"Force: z={z_force}")
            time.sleep(0.5)

        loadread.moveToForce(10,0,0) #x方向を動かす
        while True:
            #loadread.res_read()
            latest_data = loadread.get_latest_data()
            if latest_data is not None:
                x_force = latest_data[0][0] #x方向の力を取得
                if x_force >= 3:
                    print(f"Set force detected: x={x_force}")
                    loadread.move_stop()
                    break
                else:
                    print(f"Force: x={x_force}")
            time.sleep(0.5)

        loadread.moveToForce(0,10,0) #y方向を動かす
        while True:
            #loadread.res_read()
            latest_data = loadread.get_latest_data()
            if latest_data is not None:
                y_force = latest_data[1][0] #x方向の力を取得
                if y_force >= 3:
                    print(f"Set force detected: y={y_force}")
                    loadread.move_stop()
                    break
                else:
                    print(f"Force: y={y_force}")
            time.sleep(0.5)

        loadread.move_xyz(25000,27000,zpos,100,100,0)
        while True:
            loadread.res_read()
            if loadread.res_read() == 'Done':
                break

        loadread.move_senpos()

    ########## CTRL+Cで終了        
    except KeyboardInterrupt:
        loadread.move_stop()
        #loadread.stop_measurement()
        print("Program interrupted")
    #######
    ##################################################################################
