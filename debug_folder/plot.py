from time import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

def lowpass(x, samplerate):

    fp = 1                         # 通過域端周波数[Hz]
    fs = 40                         # 阻止域端周波数[Hz]
    gpass = 1                       # 通過域最大損失量[dB]
    gstop = 40                      # 阻止域最小減衰量[dB]
    # 時系列のサンプルデータ作成

    n = len(x[:, 0])                         # データ数
    dt = 1/samplerate                       # サンプリング間隔
    fn = 1/(2*dt)                   # ナイキスト周波数
    t = np.linspace(1, n, n)*dt-dt

    #print('t=',t)
    data_lp = np.array([[0]*3 for i in range(n)], dtype='float32')

    # 正規化
    Wp = fp/fn
    Ws = fs/fn

    # ローパスフィルタで波形整形
    # バターワースフィルタ
    N, Wn = signal.buttord(Wp, Ws, gpass, gstop)
    b1, a1 = signal.butter(N, Wn, "low")
    data_lp[:, 0]= signal.filtfilt(b1, a1, x[:, 0])
    data_lp[:, 1]= signal.filtfilt(b1, a1, x[:, 1])
    data_lp[:, 2]= signal.filtfilt(b1, a1, x[:, 2])
    return data_lp, t

#input_csv = pd.read_csv('gomi/gomi_404.csv')
input_csv = pd.read_csv('gomi/gomi_406.csv')

matrix_df = pd.DataFrame(input_csv)
data = matrix_df[['1', '2', '3']].values 


dataG, t = lowpass(data, 2000)

# print(data[:, 0])
wave = dataG[:, 0]
time = np.arange(wave.shape[0])
# print(time)
sec = time / 2000


dataG[:, 0] = dataG[:, 0] - np.mean(dataG[500:1000, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
dataG[:, 1] = dataG[:, 1] - np.mean(dataG[500:1000, 1])  #それを全データから差し引きする。
dataG[:, 2] = dataG[:, 2] - np.mean(dataG[500:1000, 2])

plt.plot(sec, dataG[:, 0])
plt.plot(sec, dataG[:, 1])
plt.plot(sec, dataG[:, 2])
plt.ylabel("Change of Loadcel (N)")
plt.xlabel("Time (sec)")
plt.legend(["X","Y","Z"])
plt.grid()
plt.show()