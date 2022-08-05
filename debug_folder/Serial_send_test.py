"""
2022/07/10（日）記入者：船橋佑｜Arduinoをpythonから制御するコード作成
"""

import serial
import time


if __name__ == '__main__':
    ser = serial.Serial("COM3", 115200) 
    time.sleep(1)
    #ser.write(bytes("cariv_start;",'utf-8'))
    ser.write(bytes("1;",'utf-8'))
    while(True):
        if ser.inWaiting():
            str_buf = ser.readline().strip().decode('utf-8')
            if str_buf == '1':
                print("carivration end")
                break
    ser.close()

    # while(True):
    #     youser_input = input()
    #     print(type(youser_input))
    #     if youser_input == "1":
    #         ser = serial.Serial("COM3", 115200) 
    #         time.sleep(1)
    #         ser.write(bytes("1",'utf-8'))
    #         print("ここにはいる")
    #         while(True):
    #             if ser.inWaiting():
    #                 str_buf = ser.readline().strip().decode('utf-8')
    #                 if str_buf == "move_x_end":
    #                     print("send_1_is_end")
    #                     break
    #         ser.close()
    #     break
