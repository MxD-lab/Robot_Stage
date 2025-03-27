import time
import os
import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import serial
import csv
import multiprocessing as mp
from datetime import datetime

def change_power(raw_data):
    ZERO1, ZERO2, ZERO3 = 0.034, 0.195, 0.450
    CAL, ZEROCAL01, ZEROCAL2 = 500, 5, 2.5

    road_mat = np.array([[0.05307, -0.00193, 0.00051],
                          [0.00058, 0.05273, 0.00123], 
                          [0.00046, 0.00011, 0.06087]], dtype=float)
    
    pow = np.zeros([3,1], dtype=float)
    pow[0] = (raw_data[0] - ZERO1) * CAL / ZEROCAL01
    pow[1] = (raw_data[1] - ZERO2) * CAL / ZEROCAL01
    pow[2] = (raw_data[2] - ZERO3) * CAL / ZEROCAL2

    res = np.dot(road_mat, pow)
    return res

# NI-DAQ のデータ収集プロセス
class DaqMeasure(mp.Process):
    def __init__(self, queue, stop_event, device_name="Dev2", channels=6, sample_rate=1000, chunk_size=100,
             filepath="C:/Users/MxD/Desktop/kkaido/", filename="daq_data_continuous.csv"):

        super().__init__()
        self.device_name = device_name
        self.channels = channels
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.filename = filename
        self.queue = queue
        self.stop_event = stop_event
        self.filepath = filepath
        self.filespace = os.path.join(filepath, filename)
        print(self.filespace)


    def run(self):
        with open(self.filename, mode='w', newline='') as file:
            print(f" CSV の保存先: {os.path.abspath(self.filename)}")

            writer = csv.writer(file)
            writer.writerow(["Timestamp"] + [f"Channel {i+1}" for i in range(self.channels)])

            with nidaqmx.Task() as task:
                for i in range(self.channels):
                    task.ai_channels.add_ai_voltage_chan(
                        f"{self.device_name}/ai{i}",
                        terminal_config=TerminalConfiguration.RSE
                    )
                task.timing.cfg_samp_clk_timing(
                    rate=self.sample_rate,
                    samps_per_chan=self.chunk_size,
                    sample_mode=AcquisitionType.CONTINUOUS
                )

                print("DAQ 測定開始")
                try:
                    while not self.stop_event.is_set():
                        self.data_chunk = np.array(task.read(number_of_samples_per_channel=self.chunk_size), dtype=float)
                        timestamp = datetime.now().strftime("%M:%S.%f")[:-3]
                        for i in range(self.chunk_size):
                            self.data = [channel_data[i] for channel_data in self.data_chunk]
                            power = change_power(self.data[0:3])
                            if self.queue.full():
                                self.queue.get()
                            self.queue.put(power)
                            for n in range(len(power)):
                                self.data[n] = power[n, 0]
                            writer.writerow([timestamp] + self.data)
                except KeyboardInterrupt:
                    print('DAQ 計測終了')

# ロボットステージの制御プロセス
class MotorControll(mp.Process):
    def __init__(self, queue, stop_event,daq_stop_event, port_xy="COM3", port_z="COM4", baudrate=9600):
        super().__init__()
        self.queue = queue
        self.port_xy = port_xy
        self.port_z = port_z
        self.baudrate = baudrate
        self.stop_event = stop_event
        self.daq_stop_event = daq_stop_event
        self.serial_xy = None
        self.serial_z = None
        super().__init__()
    def open_ports(self):
        """ シリアルポートを開く """
        try:
            self.serial_xy = serial.Serial(
                port=self.port_xy,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=True,  # ハードウェアフロー制御を有効化
                timeout=1.0
            )
            print(f"ポート {self.port_xy} を開きました。")

            self.serial_z = serial.Serial(
                port=self.port_z,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=True,  # ハードウェアフロー制御を有効化
                timeout=1.0
            )
            print(f"ポート {self.port_z} を開きました。")

        except serial.SerialException as e:
            print(f"⚠ ポートを開けませんでした: {e}")

    def close_ports(self):
        """ シリアルポートを閉じる """
        if self.serial_xy and self.serial_xy.is_open:
            self.serial_xy.close()
            print(f"ポート {self.port_xy} を閉じました。")
        if self.serial_z and self.serial_z.is_open:
            self.serial_z.close()
            print(f"ポート {self.port_z} を閉じました。")

    def send_command(self, ser, command):
        """ シリアルポートへコマンドを送信し、応答を受け取る """
        if ser is None or not ser.is_open:
            print("⚠ シリアルポートが開かれていません！")
            return None

        print(f"コマンド送信: {command.strip()}")
        ser.write(command.encode('utf-8'))
        ser.flush()  # バッファをクリアして送信
        time.sleep(0.2)  # 応答待ち

        if ser.in_waiting > 0:
            response = ser.read_all().decode('utf-8').strip()
            print(f"受信データ: {response}")
            return response
        else:
            print("⚠ デバイスからの応答なし")
            return None

    #####Z方向の移動方向と移動スピードと移動量を指定し実行するコマンド　directionが方向　speedが速さ　movementが移動量
    def moveZ(self, direction, speed, movement):
        """
        Parameters:
            direction (str): "+" か "-"（上 or 下）
            speed (int): 移動速度
            movement (int): 移動量（正の整数）
        """
        if direction not in ["+", "-"]:
            raise ValueError("direction は '+' または '-' で指定してください")
        if speed <= 0 or movement <= 0:
            raise ValueError("speed と movement は正の整数で指定してください")

        speed_command = f"S:J{speed}\r\n"
        move_command = f"M:1{direction}P{movement}\r\n"
        drive_command = "G:\r\n"
        confirmation_command_state = "!:\r\n"  # State check

        self.send_command(self.serial_z, speed_command)
        self.send_command(self.serial_z, move_command)
        self.send_command(self.serial_z, drive_command)
        self.send_command(self.serial_z, confirmation_command_state)

    def moveXY(self, direction_x, direction_y, speed_x, speed_y, movement_x, movement_y):

        """
        XY軸の制御コマンドを生成

        Parameters:
            direction_x (str): '+' または '-'（X軸方向）
            direction_y (str): '+' または '-'（Y軸方向）
            speed_x, speed_y (int): 速度
            movement_x, movement_y (int): 移動量

        """

        if direction_x not in ['+', '-'] or direction_y not in ['+', '-']:
            raise ValueError("direction_x, direction_y は '+' または '-' にしてください")
        if speed_x <= 0 or speed_y <= 0 or movement_x <= 0 or movement_y <= 0:
            raise ValueError("速度・移動量はすべて正の整数である必要があります")

        # 速度指定コマンド
        speed_command = f"S:W+J{'' if direction_x == '+' else '-'}{speed_x}{'' if direction_y == '+' else '-'}{speed_y}\r\n"

        # 移動量コマンド
        move_command = f"M:W+P{'' if direction_x == '+' else '-'}{movement_x}{'' if direction_y == '+' else '-'}{movement_y}\r\n"

        # 駆動開始
        drive_command = "G:\r\n"
        confirmation_command_state = "!:\r\n"  # State check

        self.send_command(self.serial_xy, speed_command)
        self.send_command(self.serial_xy, move_command)
        self.send_command(self.serial_xy, drive_command)
        self.send_command(self.serial_xy, confirmation_command_state)




    def stop(self):##ロボットステージをとめるコード
        print("ロボットステージ停止")
        confirmation_command_stop = "L:E"  # キャリブレーション
        self.send_command(self.serial_z, confirmation_command_stop)
        self.send_command(self.serial_xy, confirmation_command_stop)

        self.close_ports()
        if self.daq_measure:
            self.daq_stop_event.set()  # DAQ計測プロセスに停止を指示
            self.daq_measure.join()    # DAQプロセスの終了を待つ
            print('Daq計測終了')

    def keep_forceZ(self,zpos,power,f):
        if power[2][0] <= f:
            zpos = zpos +1
            self.moveZ("-", 2000, 1)
        else:
            time.sleep(1)
        return zpos
        

    def calibration(self):
        print("キャリブレーション開始")
        
        #設定コマンド一覧
        confirmation_command_cal_xy = "H:W-+\r\n"  # キャリブレーション
        confirmation_command_speed = "S:J2000\r\n"  # Speed setting
        confirmation_command_Z = "M:1+P80000\r\n"  # Move amount
        confirmation_command_drive = "G:\r\n"  # Start drive
        confirmation_command_state = "!:\r\n"  # State check
       

        # Z-axis calibration
        self.moveZ("+", 2000, 80000)
        time.sleep(2)
        
        # XY-axis calibration
        self.send_command(self.serial_xy, confirmation_command_speed)
        self.send_command(self.serial_xy, confirmation_command_cal_xy)
        self.send_command(self.serial_xy, confirmation_command_drive)

    #####キャリブレーション後に最初に設定する関数
    def move_first(self):   

        # nresponce_z = 0 #z軸が動作準備中になっているかを判定する変数　３回応答ないと終了
        # nresponce_xy = 0 #xy軸が動作準備中になっているかを判定する変数　３回応答ないと終了

        # response_z = self.send_command(self.serial_z, confirmation_command_state)
        # if response_z !="R" :
        #     time.sleep(1)  # Sleep time based on response handling
        #     nresponce_z = nresponce_z + 1
        #     if nresponce_z >= 3 :
        #         print("Z軸のロボットステージが動作しているか反応がありません")

        # response_xy = self.send_command(self.serial_xy, confirmation_command_state)
        # if response_xy !="R" :
        #     time.sleep(1)  # Sleep time based on response handling
        #     nresponce_xy = nresponce_xy + 1
        #     if nresponce_xy >= 3 :
        #         print("xy軸のロボットステージが動作しているか反応がありません")


        print("初期移動開始")
        #設定コマンド一覧
        confirmation_command_speed = "S:J2000\r\n"  # Speed setting
        confirmation_command_Z_move = "M:1-P60000\r\n"  # Move amount
        confirmation_command_XY_move = "M:W+P50000-P60000\r\n"  # Move amount
        confirmation_command_drive = "G:\r\n"  # Start drive
        confirmation_command_state = "!:\r\n"  # State check

        self.send_command(self.serial_z, confirmation_command_state)
        # XY adjustment
        self.send_command(self.serial_xy, confirmation_command_state)
        self.send_command(self.serial_xy, confirmation_command_speed)
        self.send_command(self.serial_xy, confirmation_command_XY_move)
        self.send_command(self.serial_xy, confirmation_command_drive)
        time.sleep(5)
        
        # Z adjustment
        self.send_command(self.serial_z, confirmation_command_speed)
        self.send_command(self.serial_z, confirmation_command_Z_move)
        self.send_command(self.serial_z, confirmation_command_drive)

    #####niでの計測をするプロセスを立てる
    def daq_start(self):
        self.daq_measure = DaqMeasure(self.queue,self.daq_stop_event)
        self.daq_measure.start()
        print('Daq 計測開始')

    def run(self):
        """ ロボットステージの動作制御 """

        #状態管理用
        state = 0

        try:
            self.open_ports()
            print("シリアル通信開始")
            self.calibration()
            time.sleep(17)
            self.move_first()
            ## daq計測開始
            time.sleep(10)
            self.daq_start() 

            #設定コマンド
            confirmation_command_speed = "S:J2000\r\n"  # 速度設定
            confirmation_command_Z_under = "M:1-P100\r\n"  # z軸を下に少し移動
            confirmation_command_Z_upper = "M:1+P100\r\n"  # z軸を上に少し移動
            confirmation_command_Z_move    = "M:1-P65000\r\n"  # 移動量指定
            confirmation_command_XY_move    = "M:W+P50000-P60000\r\n"  # 移動量指定
            confirmation_command_drive = "G:\r\n"  # 駆動開始
            confirmation_command_state = "!:\r\n" #状態確認

            while not self.stop_event.is_set():
                power = self.queue.get()
                print(f"受信データ: {power}")
                
                response_z = self.send_command(self.serial_z, confirmation_command_state)
                if response_z !="R" :
                    time.sleep(0.5)  # Sleep time based on response handling
                    continue

                if state == 0:
                    print("down")
                    if power[2][0] >= 3:
                        self.stop()
                        break
                    elif power[2][0] <= 1:
                        self.send_command(self.serial_z, confirmation_command_Z_under)
                        self.send_command(self.serial_z, confirmation_command_speed)
                        self.send_command(self.serial_z, confirmation_command_drive)
                        #print("b")
                    elif power[2][0] >= 1.1:
                        self.send_command(self.serial_z, confirmation_command_Z_upper)
                        self.send_command(self.serial_z, confirmation_command_speed)
                        self.send_command(self.serial_z, confirmation_command_drive)     
                    else:
                        state +=1
                        #print("c")
                elif state == 1:
                    for i in range(10):
                        power = self.queue.get()
                        zpos = self.keep_forceZ(zpos,power,1)
                    state += 1                    
                elif state == 2:
                    if power[2][0] <= 5:
                        zpos = zpos +1
                        self.moveZ(zpos,0,0,10)
                    else:
                        state +=1
                # elif state == 3:
                #     for i in range(10):
                #         power = self.queue.get()
                #         zpos = self.keep_forceZ(xpos,ypos,zpos,power,5)
                #     state += 1
                # elif state == 4:
                #     if power[2][0] >= 3:
                #         zpos = zpos -1
                #         self.move_xyz(xpos,ypos,zpos,0,0,10)
                #     else:
                #         state += 1
                # elif state == 5:
                #     # if power[0][0] <= 2:
                #     for i in range(100):
                #         xpos = xpos -1
                #         self.move_xyz(xpos,ypos,zpos,10,0,0)
                #     # else:
                #         #state +=1
                #     state += 1
                # elif state == 6:
                #     for i in range(50):
                #         ypos = ypos + 1
                #         self.move_xyz(xpos,ypos,zpos,0,10,0)
                #     state += 1
                # elif state ==7:
                #     for i in range(200):
                #         ypos = ypos + 1
                #         xpos = xpos - 1
                #         self.move_xyz(xpos,ypos,zpos,10,10,0)
                #     state +=1
                # elif state == 8:
                #     self.move_xyz(25000,27000,36000,20,20,20)
                #     state +=1
                elif state ==1:
                    print("d")
                    break  
            print('試行終了')

        except KeyboardInterrupt:
            print("停止")
        finally:
            self.close_ports()
            ##ロボットステージを上にあげるコードを書く　
            if self.daq_measure:
                self.daq_stop_event.set()  # DAQ計測プロセスに停止を指示
                self.daq_measure.join()    # DAQプロセスの終了を待つ
                print('Daq計測終了')

            



if __name__ == '__main__':
    queue = mp.Queue(3)
    stop_event = mp.Event()
    daq_stop_event = mp.Event()
    

    print("モータ制御プロセスを開始...")
    motor = MotorControll(queue, stop_event, daq_stop_event, port_xy="COM3", port_z="COM4")

    try:
        motor.start()

    except KeyboardInterrupt:
        stop_event.set()
        daq_stop_event.set()
        print("終了処理中...")
    finally:
        motor.join()
        print('プログラム終了')


