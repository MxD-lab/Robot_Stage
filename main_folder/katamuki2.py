# coding: UTF-8

import numpy as np
import sklearn
#print(sklearn.__version__)
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
import pandas as pd
import csv
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV

from scipy import signal
import glob
import sys
import math
from scipy.interpolate import interp1d

def reg1dim(x, y):
    a = np.dot(x, y)/ (x ** 2).sum()
    return a

fig = plt.figure(figsize=(10,7)) #グラフ表示の枠を調節
fig.subplots_adjust(hspace=0.3, wspace=0.2) #グラフ間の距離を調節
ax1 = fig.add_subplot(3, 3, 1) #グラフの分割表示
ax2 = fig.add_subplot(3, 3, 2)
ax3 = fig.add_subplot(3, 3, 3)
ax4 = fig.add_subplot(3, 3, 4)
ax5 = fig.add_subplot(3, 3, 5)
ax6 = fig.add_subplot(3, 3, 6)
ax7 = fig.add_subplot(3, 3, 7)
ax8 = fig.add_subplot(3, 3, 8)
ax9 = fig.add_subplot(3, 3, 9)


#まずはデータの読み込みから
df_header = pd.read_csv('Nii_data/gomiX_21.csv')      #CSVファイル読み込みxの分
df_header.columns=['1','2','3','4','5','6']
matrix_df = pd.DataFrame(df_header)

df_header2 = pd.read_csv('Nii_data/gomiY_6.csv')      #CSVファイル読み込みyの分
df_header2.columns=['1','2','3','4','5','6']
matrix_df2 = pd.DataFrame(df_header2)

df_header3 = pd.read_csv('Nii_data/gomiZ_11.csv')      #CSVファイル読み込みzの分
df_header3.columns=['1','2','3','4','5','6']
matrix_df3 = pd.DataFrame(df_header3)
#matrix_df[matrix_df['3'] < 3]

df_header4 = pd.read_csv('Nii_data/gomiXYZ_19.csv')      #CSVファイル読み込み計測テストのぶん
df_header4.columns=['1','2','3','4','5','6']
matrix_df4 = pd.DataFrame(df_header4)

#線形回帰モデルの構築
#lr = SGDRegressor(max_iter = 100)
#lr = make_pipeline(StandardScaler(),SGDRegressor(max_iter=1000, tol=1e-3))
lr = LinearRegression()
lr2 = LinearRegression()
lr3 = LinearRegression()
lr4 = LinearRegression()
lr5 = LinearRegression()
lr6 = LinearRegression()
lr7 = LinearRegression()
lr8 = LinearRegression()
lr9 = LinearRegression()

X = matrix_df[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 x
Y_true = matrix_df[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])

#X = X[10000:]  #ローパスで急に数値が下がるのを除く
#Y_true =Y_true[10000:]

Y_true[:,0] = Y_true[:,0]*0.87
Y_true[:,1] = Y_true[:,1]*0.87

X2 = matrix_df2[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 y
Y2_true = matrix_df2[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])

#X2 = X2[10000:]  #ローパスで急に数値が下がるのを除く
#Y2_true =Y2_true[10000:]

Y2_true[:,0] = Y2_true[:,0]*0.87
Y2_true[:,1] = Y2_true[:,1]*0.87

X3 = matrix_df3[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 z
Y3_true = matrix_df3[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])

#X3 = X3[10000:]  #ローパスで急に数値が下がるのを除く
#Y3_true =Y3_true[10000:]

Y3_true[:,0] = Y3_true[:,0]*0.87
Y3_true[:,1] = Y3_true[:,1]*0.87


#matrix_df4 = pd.concat([matrix_df, matrix_df2, matrix_df3], axis=0) #1軸ずつのデータを合成

X4 = matrix_df4[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 テスト
Y4_true = matrix_df4[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値　テスト
#print(Y_true[0,0])

#X4 = X4[10000:]  #ローパスで急に数値が下がるのを除く
#Y4_true =Y4_true[10000:]

Y4_true[:,0] = Y4_true[:,0]*0.87
Y4_true[:,1] = Y4_true[:,1]*0.87


#print(Y_true[0,0])
###################################################
# パラメータ設定
def lowpass(x, samplerate):

    fp = 1                         # 通過域端周波数[Hz]
    fs = 40                         # 阻止域端周波数[Hz]
    gpass = 1                       # 通過域最大損失量[dB]
    gstop = 40                      # 阻止域最小減衰量[dB]
    # 時系列のサンプルデータ作成

    n = len(x[:,0])                         # データ数
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
    data_lp[:,0]= signal.filtfilt(b1, a1, x[:,0])
    data_lp[:,1]= signal.filtfilt(b1, a1, x[:,1])
    data_lp[:,2]= signal.filtfilt(b1, a1, x[:,2])
    return data_lp, t

####################################################

#print('Xshape = ', X.shape)
#print('Y_trueshape = ', Y_true.shape)


#生データ確認(カンチレバー時系列)


#XG, t1c1 = lowpass(X, 1000) //ローパスが原因で描画できないので消す(9/1
#XG2, t1c2 = lowpass(X2, 1000)
#XG3, t1c3 = lowpass(X3, 1000)
#XG4, t1c3 = lowpass(X4, 1000)

XG = X
XG2 = X2
XG3 = X3
XG4 = X4

#print('X = ', X)
#print('XG = ', XG)
#XG[:,0]=XG[:,0]*10
#XG[:,1]=XG[:,1]*2

XG[:, 0] = XG[:, 0] - np.mean(XG[:100, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
XG[:, 1] = XG[:, 1] - np.mean(XG[:100, 1])  #それを全データから差し引きする。
XG[:, 2] = XG[:, 2] - np.mean(XG[:100, 2])
x1c1 = XG[:, 0]
x2c1 = XG[:, 1]
x3c1 = XG[:, 2]

XG2[:, 0] = XG2[:, 0] - np.mean(XG2[:100, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
XG2[:, 1] = XG2[:, 1] - np.mean(XG2[:100, 1])  #それを全データから差し引きする。
XG2[:, 2] = XG2[:, 2] - np.mean(XG2[:100, 2])
x1c2 = XG2[:, 0]
x2c2 = XG2[:, 1]
x3c2 = XG2[:, 2]

XG3[:, 0] = XG3[:, 0] - np.mean(XG3[:100, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
XG3[:, 1] = XG3[:, 1] - np.mean(XG3[:100, 1])  #それを全データから差し引きする。
XG3[:, 2] = XG3[:, 2] - np.mean(XG3[:100, 2])
x1c3 = XG3[:, 0]
x2c3 = XG3[:, 1]
x3c3 = XG3[:, 2]

x1 = XG4[:, 0] - np.mean(XG4[:100, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
x2 = XG4[:, 1] - np.mean(XG4[:100, 1])  #それを全データから差し引きする。
x3 = XG4[:, 2] - np.mean(XG4[:100, 2])


#XGX = np.array([[0]*3 for i in range(len(x1))], dtype='float32')
#XGX[:, 0] = x1
#XGX[:, 1] = x2
#XGX[:, 2] = x3
#print(x1)
#print(XGX)

#y = range(len(x1))
xgc1 = np.arange(x1c1.shape[0])
xgc1 = xgc1 / 1000

xgc2 = np.arange(x1c2.shape[0])
xgc2 = xgc2 / 1000

xgc3 = np.arange(x1c3.shape[0])
xgc3 = xgc3 / 1000

timec = np.arange(XG4.shape[0])
timec = timec / 1000

#print('x1shape = ', x1.shape)
#print('x2shape = ', x2.shape)
#print('x3shape = ', x3.shape)

'''
ax1.plot(timec, x1)
ax1.plot(timec, x2)
ax1.plot(timec, x3)


ax1.set_ylabel("Change of Voltage (V)")
ax1.set_xlabel("Time (sec)")
ax1.legend(["1 axis","2 axis","3 axis"])
ax1.grid() #グリッド線をつける
ax1.set_title("sensor_Time series")
'''

#生データ確認(ロードセル時系列)

#YG_true, t2c1 = lowpass(Y_true, 1000)
YG_true = Y_true
x4c1 = YG_true[:, 0]
x5c1 = YG_true[:, 1]
x6c1 = YG_true[:, 2]

#YG2_true, t2c2 = lowpass(Y2_true, 1000)
YG2_true = Y2_true
x4c2 = YG2_true[:, 0]
x5c2 = YG2_true[:, 1]
x6c2 = YG2_true[:, 2]

#YG3_true, t2c3 = lowpass(Y3_true, 1000)
YG3_true = Y3_true
x4c3 = YG3_true[:, 0]
x5c3 = YG3_true[:, 1]
x6c3 = YG3_true[:, 2]

#YG4_true, n = lowpass(Y4_true, 1000)
YG4_true = Y4_true
x4 = YG4_true[:, 0]
x5 = YG4_true[:, 1]
x6 = YG4_true[:, 2]

#xg = range(len(x4))

#print('x4shape = ', x4.shape[0])
#print('x5shape = ', x5.shape)
#print('x6shape = ', x6.shape)
#xg = np.arange(x4.shape[0])
#xg = xg / 1000
'''
ax2.set_ylim([-1.5, 3])
ax2.plot(timec, x4)
ax2.plot(timec, x5)
ax2.plot(timec, x6)

ax2.set_ylabel("Change of Loadcel (N)")
ax2.set_xlabel("Time (sec)")
ax2.legend(["X","Y","Z"])
ax2.grid() #グリッド線をつける
ax2.set_title("roadcell_Time series")
'''
#学習

lr.fit(YG_true[:, 0].reshape(-1, 1), XG[:, 0].reshape(-1, 1))
lr2.fit(YG_true[:, 0].reshape(-1, 1), XG[:, 1].reshape(-1, 1))
lr3.fit(YG_true[:, 0].reshape(-1, 1), XG[:, 2].reshape(-1, 1))
lr4.fit(YG2_true[:, 1].reshape(-1, 1), XG2[:, 0].reshape(-1, 1))
lr5.fit(YG2_true[:, 1].reshape(-1, 1), XG2[:, 1].reshape(-1, 1))
lr6.fit(YG2_true[:, 1].reshape(-1, 1), XG2[:, 2].reshape(-1, 1))

#lr7.fit(XG3[:, 0].reshape(-1, 1), YG3_true[:, 2].reshape(-1, 1))
lr7.fit(YG3_true[:, 2].reshape(-1, 1), XG3[:, 0].reshape(-1, 1))
lr8.fit(YG3_true[:, 2].reshape(-1, 1), XG3[:, 1].reshape(-1, 1))
lr9.fit(YG3_true[:, 2].reshape(-1, 1), XG3[:, 2].reshape(-1, 1))

#print(XG)
#print(YG_true)


matrix = np.array([[lr.coef_[0, 0], lr4.coef_[0, 0], lr7.coef_[0, 0]],
                    [lr2.coef_[0, 0], lr5.coef_[0, 0], lr8.coef_[0, 0]], 
                    [lr3.coef_[0, 0], lr6.coef_[0, 0], lr9.coef_[0, 0]]])
'''
matrix = np.array([[lr.coef_[0, 0], lr2.coef_[0, 0], lr3.coef_[0, 0]],
                    [lr4.coef_[0, 0], lr5.coef_[0, 0], lr6.coef_[0, 0]], 
                    [lr7.coef_[0, 0], lr8.coef_[0, 0], lr9.coef_[0, 0]]])
'''

print(matrix)

ax1.scatter(YG_true[:, 0], XG[:, 0], s=5)
ax1.grid()
print(YG_true[:, 0].shape[0])
#dy = range(YG_true[:, 0].shape[0])
dy = np.arange(-5, 50, 1)
#ax1.plot(XG[:, 0], lr.predict(XG[:, 0].reshape(-1, 1)), color='#ff4500')
ax1.plot(dy, dy*lr.coef_[0, 0], color='#ff4500')
ax1.scatter(YG_true[0, 0], XG[0, 0], s=30, c="red")      #一番最初のデータを黄色でマーク
ax1.set_xlim([-0.4, 1.0])
ax1.set_ylim([-1.0, 1.0])
ax1.set_ylabel("Cantilever Ch1 (V)")


print(lr.coef_[0, 0])

ax2.scatter(YG2_true[:, 1], XG2[:, 0], s=5)
ax2.grid()
print(lr2.coef_[0, 0])
dy = np.arange(-5, 50, 1)
#ax2.plot(XG2[:, 0], lr4.predict(XG2[:, 0].reshape(-1, 1)), color='#ff4500')
ax2.plot(dy, dy*lr4.coef_[0, 0], color='#ff4500')
ax2.scatter(YG2_true[0, 1], XG2[0, 0], s=30, c="red")      #一番最初のデータを黄色でマーク
ax2.set_xlim([-0.4, 1.0])
ax2.set_ylim([-1.0, 1.0])
#ax2.set_ylabel("LoadcelX (N)")


ax3.scatter(YG3_true[:, 2], XG3[:, 0], s=5)
ax3.grid()
dy = np.arange(-5, 50, 1)
print(lr3.coef_[0, 0])
#ax3.plot(XG3[:, 0], a*XG3[:, 0], color='#ff4500')
ax3.plot(dy, dy*lr7.coef_[0, 0], color='#ff4500')
print('a')
ax3.scatter(YG3_true[0, 2], XG3[0, 0], s=30, c="red")      #一番最初のデータを黄色でマーク
ax3.set_xlim([-0.5, 5.0])
ax3.set_ylim([-0.2, 1.5])
#ax3.set_ylabel("LoadcelX (N)")



ax4.scatter(YG_true[:, 0], XG[:, 1], s=5)
ax4.grid()
dy = np.arange(-5, 50, 1)
#ax4.plot(XG[:, 1], lr2.predict(XG[:, 1].reshape(-1, 1)), color='#ff4500')
ax4.plot(dy, dy*lr2.coef_[0, 0], color='#ff4500')
ax4.scatter(YG_true[0, 0], XG[0, 1], s=30, c="red")      #一番最初のデータを黄色でマーク
ax4.set_xlim([-0.4, 1.0])
ax4.set_ylim([-1.0, 1.0])
ax4.set_ylabel("Cantilever Ch2 (V)")


ax5.scatter(YG2_true[:, 1], XG2[:, 1], s=5)
ax5.grid()
#dy = range(YG2_true[:, 1].shape[0])
dy = np.arange(-5, 50, 1)
#ax5.plot(XG2[:, 1], lr5.predict(XG2[:, 1].reshape(-1, 1)), color='#ff4500')
ax5.plot(dy, dy*lr5.coef_[0, 0], color='#ff4500')
ax5.scatter(YG2_true[0, 1], XG2[0, 1], s=30, c="red")      #一番最初のデータを黄色でマーク
ax5.set_xlim([-0.4, 1.0])
ax5.set_ylim([-1.0, 1.0])



ax6.scatter(YG3_true[:, 2], XG3[:, 1], s=5)
ax6.grid()
#dy = range(YG2_true[:, 1].shape[0])
dy = np.arange(-5, 50, 1)
ax6.plot(dy, dy*lr8.coef_[0, 0], color='#ff4500')
#ax6.plot(XG3[:, 1], lr8.predict(XG3[:, 1].reshape(-1, 1)), color='#ff4500')
ax6.scatter(YG3_true[0, 2], XG3[0, 1], s=30, c="red")      #一番最初のデータを黄色でマーク
ax6.set_xlim([-0.5, 5.0])
ax6.set_ylim([-0.2, 1.5])


ax7.scatter(YG_true[:, 0], XG[:, 2], s=5)
ax7.grid()
dy = np.arange(-5, 50, 1)
#ax7.plot(XG[:, 2], lr3.predict(XG[:, 2].reshape(-1, 1)), color='#ff4500')
ax7.plot(dy, dy*lr3.coef_[0, 0], color='#ff4500')
ax7.scatter(YG_true[0, 0], XG[0, 2], s=30, c="red")      #一番最初のデータを黄色でマーク
ax7.set_xlim([-0.4, 1.0])
ax7.set_ylim([-1.0, 1.0])
ax7.set_ylabel("Cantilever Ch3 (V)")
ax7.set_xlabel("LoadcelX (N)")


ax8.scatter(YG2_true[:, 1], XG2[:, 2], s=5)
ax8.grid()
dy = np.arange(-5, 50, 1)
#ax8.plot(XG2[:, 2], lr6.predict(XG2[:, 2].reshape(-1, 1)), color='#ff4500')
ax8.plot(dy, dy*lr6.coef_[0, 0], color='#ff4500')
ax8.scatter(YG2_true[0, 1], XG2[0, 2], s=30, c="red")      #一番最初のデータを黄色でマーク
ax8.set_xlim([-0.4, 1.0])
ax8.set_ylim([-1.0, 1.0])
ax8.set_xlabel("LoadcelY (N)")

ax9.scatter(YG3_true[:, 2], XG3[:, 2], s=5)
ax9.grid()
dy = np.arange(-5, 50, 1)
#ax9.plot(XG3[:, 2], lr9.predict(XG3[:, 2].reshape(-1, 1)), color='#ff4500')
ax9.plot(dy, dy*lr9.coef_[0, 0], color='#ff4500')
ax9.scatter(YG3_true[0, 2], XG3[0, 2], s=30, c="red")      #一番最初のデータを黄色でマーク
ax9.set_xlim([-0.5, 5.0])
ax9.set_ylim([-0.2, 1.5])
ax9.set_xlabel("LoadcelZ (N)")

plt.show()

#ここから校正処理用の生データの確認

fig2 = plt.figure(figsize=(10,7)) #グラフ表示の枠を調節
fig2.subplots_adjust(hspace=0.3, wspace=0.2) #グラフ間の距離を調節
ax1 = fig2.add_subplot(3, 3, 1) #グラフの分割表示
ax2 = fig2.add_subplot(3, 3, 2)
ax3 = fig2.add_subplot(3, 3, 3)
ax4 = fig2.add_subplot(3, 3, 4)
ax5 = fig2.add_subplot(3, 3, 5)
ax6 = fig2.add_subplot(3, 3, 6)
ax7 = fig2.add_subplot(3, 3, 7)
ax8 = fig2.add_subplot(3, 3, 8)
ax9 = fig2.add_subplot(3, 3, 9)

#力が混ざったデータなので時間で切り分ける
c1x = x1[22000:30000]
c1y = x1[13000:21000]
c1z = x1[500:12000]

c2x = x2[22000:30000]
c2y = x2[13000:21000]
c2z = x2[500:12000]

c3x = x3[22000:30000]
c3y = x3[13000:21000]
c3z = x3[500:12000]

x4 = x4[22000:30000]
x5 = x5[13000:21000]
x6 = x6[500:12000]

ax1.scatter(x4, c1x, s=5, c="red")
ax1.grid()
ax1.scatter(x4[0], c1x[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax1.set_xlim([-1.5, 1.5])
ax1.set_ylim([-1.0, 1.0])
ax1.set_ylabel("Shokkaku c1 (V)")




ax2.scatter(x5, c1y, s=5, c="red")
ax2.grid()
ax2.scatter(x5[0], c1y[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax2.set_xlim([-1.5, 1.5])
ax2.set_ylim([-0.5, 0.5])
#ax2.set_ylabel("LoadcelX (N)")


ax3.scatter(x6, c1z, s=5, c="red")
ax3.grid()
ax3.scatter(x6[0], c1z[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax3.set_xlim([-1.5, 1.5])
ax3.set_ylim([-0.5, 0.5])
#ax3.set_ylabel("LoadcelX (N)")



ax4.scatter(x4, c2x, s=5, c="red")
ax4.grid()
ax4.scatter(x4[0], c2x[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax4.set_xlim([-1.5, 1.5])
ax4.set_ylim([-0.5, 0.5])
ax4.set_ylabel("Shokkaku c2 (V)")


ax5.scatter(x5, c2y, s=5, c="red")
ax5.grid()
ax5.scatter(x5[0], c2y[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax5.set_xlim([-1.5, 1.5])
ax5.set_ylim([-0.5, 0.5])



ax6.scatter(x6, c2z, s=5, c="red")
ax6.grid()
ax6.scatter(x6[0], c2z[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax6.set_xlim([-1.5, 1.5])
ax6.set_ylim([-0.5, 0.5])


ax7.scatter(x4, c3x, s=5, c="red")
ax7.grid()
ax7.scatter(x4[0], c3x[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax7.set_xlim([-1.5, 1.5])
ax7.set_ylim([-0.5, 0.5])
ax7.set_ylabel("Shokkaku c3 (V)")
ax7.set_xlabel("LoadcelX (N)")


ax8.scatter(x5, c3y, s=5, c="red")
ax8.grid()
ax8.scatter(x5[0], c3y[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax8.set_xlim([-1.5, 1.5])
ax8.set_ylim([-0.5, 0.5])
ax8.set_xlabel("LoadcelY (N)")

ax9.scatter(x6, c3z, s=5, c="red")
ax9.grid()
ax9.scatter(x6[0], c3z[0], s=30, c="blue")      #一番最初のデータを黄色でマーク
ax9.set_xlim([-1.5, 1.5])
ax9.set_ylim([-0.5, 0.5])
ax9.set_xlabel("LoadcelZ (N)")


plt.show()
