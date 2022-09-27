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

fig = plt.figure(figsize=(10,7)) #グラフ表示の枠を調節
fig.subplots_adjust(hspace=0.3, wspace=0.2) #グラフ間の距離を調節
ax1 = fig.add_subplot(2, 2, 1) #グラフの分割表示
ax2 = fig.add_subplot(2, 2, 2)
ax3 = fig.add_subplot(2, 2, 3)
ax4 = fig.add_subplot(2, 2, 4)
#ax5 = fig.add_subplot(3, 3, 5)
#ax6 = fig.add_subplot(3, 3, 6)
#ax7 = fig.add_subplot(3, 3, 7)
#ax8 = fig.add_subplot(3, 3, 8)
#ax9 = fig.add_subplot(3, 3, 9)


#まずはデータの読み込みから
df_header = pd.read_csv('Nii_data/data/9-23/gomiX_7.csv')      #CSVファイル読み込みxの分
df_header.columns=['1','2','3','4','5','6']
matrix_df = pd.DataFrame(df_header)

df_header2 = pd.read_csv('Nii_data/data/9-23/gomiY_1.csv')      #CSVファイル読み込みyの分
df_header2.columns=['1','2','3','4','5','6']
matrix_df2 = pd.DataFrame(df_header2)

df_header3 = pd.read_csv('Nii_data/data/9-23/gomiZ_7.csv')      #CSVファイル読み込みzの分
df_header3.columns=['1','2','3','4','5','6']
matrix_df3 = pd.DataFrame(df_header3)
#matrix_df[matrix_df['3'] < 3]

df_header4 = pd.read_csv('Nii_data/data/9-23/gomiXYZ_6.csv')      #CSVファイル読み込み計測テストのぶん
df_header4.columns=['1','2','3','4','5','6']
matrix_df4 = pd.DataFrame(df_header4)

#線形回帰モデルの構築
#lr = SGDRegressor(max_iter = 100)
#lr = make_pipeline(StandardScaler(),SGDRegressor(max_iter=1000, tol=1e-3))

lr = LinearRegression(fit_intercept=False)
lr2 = LinearRegression(fit_intercept=False)
lr3 = LinearRegression(fit_intercept=False)
lr4 = LinearRegression(fit_intercept=False)
lr5 = LinearRegression(fit_intercept=False)
lr6 = LinearRegression(fit_intercept=False)
lr7 = LinearRegression(fit_intercept=False)
lr8 = LinearRegression(fit_intercept=False)
lr9 = LinearRegression(fit_intercept=False)
'''
lr = LinearRegression()
lr2 = LinearRegression()
lr3 = LinearRegression()
lr4 = LinearRegression()
lr5 = LinearRegression()
lr6 = LinearRegression()
lr7 = LinearRegression()
lr8 = LinearRegression()
lr9 = LinearRegression()
'''

X = matrix_df[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 x
Y_true = matrix_df[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])
#Y_true[:,0] = Y_true[:,0]*0.87             #ロードセルの値がモーメントだった場合にいるはずの補正
#Y_true[:,1] = Y_true[:,1]*0.87

X2 = matrix_df2[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 y
Y2_true = matrix_df2[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])
#Y2_true[:,0] = Y2_true[:,0]*0.87
#Y2_true[:,1] = Y2_true[:,1]*0.87

X3 = matrix_df3[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 z
Y3_true = matrix_df3[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値
#print(Y_true[0,0])
#Y3_true[:,0] = Y3_true[:,0]*0.87
#Y3_true[:,1] = Y3_true[:,1]*0.87


#matrix_df4 = pd.concat([matrix_df, matrix_df2, matrix_df3], axis=0) #1軸ずつのデータを合成

X4 = matrix_df4[['4', '5', '6']].values         # 説明変数（Numpyの配列）センサの値 テスト
Y4_true = matrix_df4[['1', '2', '3']].values         # 目的変数（Numpyの配列）ロードセルの値　テスト
#print(Y_true[0,0])

#X4 = X4[15000:]  #ローパスで急に数値が下がるのを除く
#Y4_true =Y4_true[15000:]

#Y4_true[:,0] = Y4_true[:,0]*0.87
#Y4_true[:,1] = Y4_true[:,1]*0.87


#print(Y_true[0,0])
###################################################
# パラメータ設定
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

####################################################

#print('Xshape = ', X.shape)
#print('Y_trueshape = ', Y_true.shape)


#生データ確認(カンチレバー時系列)


XG, t1c1 = lowpass(X, 2000) #ローパスが原因で描画できないので消す(9/1
XG2, t1c2 = lowpass(X2, 2000)
XG3, t1c3 = lowpass(X3, 2000)
XG4, t1c3 = lowpass(X4, 2000)

# XG = X
# XG2 = X2
# XG3 = X3
# XG4 = X4

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

XG4[:, 0] = XG4[:, 0] - np.mean(XG4[:100, 0])  #風袋をとる、前100個のデータを取り平均値を出す。
XG4[:, 1] = XG4[:, 1] - np.mean(XG4[:100, 1])  #それを全データから差し引きする。
XG4[:, 2] = XG4[:, 2] - np.mean(XG4[:100, 2])
x1 = XG4[:, 0]
x2 = XG4[:, 1]
x3 = XG4[:, 2]

#XGX = np.array([[0]*3 for i in range(len(x1))], dtype='float32')
#XGX[:, 0] = x1
#XGX[:, 1] = x2
#XGX[:, 2] = x3
#print(x1)
#print(XGX)

#y = range(len(x1))
xgc1 = np.arange(x1c1.shape[0])
xgc1 = xgc1 / 2000

xgc2 = np.arange(x1c2.shape[0])
xgc2 = xgc2 / 2000

xgc3 = np.arange(x1c3.shape[0])
xgc3 = xgc3 / 2000

timec = np.arange(XG4.shape[0])
timec = timec / 2000

#print('x1shape = ', x1.shape)
#print('x2shape = ', x2.shape)
#print('x3shape = ', x3.shape)


ax1.plot(timec, x1)
ax1.plot(timec, x2)
ax1.plot(timec, x3)


ax1.set_ylabel("Change of Voltage (V)")
ax1.set_xlabel("Time (sec)")
ax1.legend(["1 axis","2 axis","3 axis"])
ax1.grid() #グリッド線をつける
ax1.set_title("sensor_Time series")


#生データ確認(ロードセル時系列)

YG_true, t2c1 = lowpass(Y_true, 2000) #ローパスが原因で描画できないので消す(9/1
# YG_true = Y_true
x4c1 = YG_true[:, 0]
x5c1 = YG_true[:, 1]
x6c1 = YG_true[:, 2]

YG2_true, t2c2 = lowpass(Y2_true, 2000)
# YG2_true = Y2_true
x4c2 = YG2_true[:, 0]
x5c2 = YG2_true[:, 1]
x6c2 = YG2_true[:, 2]

YG3_true, t2c3 = lowpass(Y3_true, 2000)
# YG3_true = Y3_true
x4c3 = YG3_true[:, 0]
x5c3 = YG3_true[:, 1]
x6c3 = YG3_true[:, 2]

YG4_true, n = lowpass(Y4_true, 2000)
# YG4_true = Y4_true
x4 = YG4_true[:, 0]
x5 = YG4_true[:, 1]
x6 = YG4_true[:, 2]

#print(x4)

#xg = range(len(x4))

#print('x4shape = ', x4.shape[0])
#print('x5shape = ', x5.shape)
#print('x6shape = ', x6.shape)
#xg = np.arange(x4.shape[0])
#xg = xg / 1000

ax2.set_ylim([-0.5, 2.5])
ax2.plot(timec, x4)
ax2.plot(timec, x5)
ax2.plot(timec, x6)

ax2.set_ylabel("Change of Loadcel (N)")
ax2.set_xlabel("Time (sec)")
ax2.legend(["X","Y","Z"])
ax2.grid() #グリッド線をつける
ax2.set_title("roadcell_Time series")

#学習

'''
lr.fit(XG[:, 0].reshape(-1, 1), YG_true[:, 0].reshape(-1, 1))
lr2.fit(XG[:, 1].reshape(-1, 1), YG_true[:, 0].reshape(-1, 1))
lr3.fit(XG[:, 2].reshape(-1, 1), YG_true[:, 0].reshape(-1, 1))

lr4.fit(XG2[:, 0].reshape(-1, 1), YG2_true[:, 1].reshape(-1, 1))
lr5.fit(XG2[:, 1].reshape(-1, 1), YG2_true[:, 1].reshape(-1, 1))
lr6.fit(XG2[:, 2].reshape(-1, 1), YG2_true[:, 1].reshape(-1, 1))

lr7.fit(XG3[:, 0].reshape(-1, 1), YG3_true[:, 2].reshape(-1, 1))
lr8.fit(XG3[:, 1].reshape(-1, 1), YG3_true[:, 2].reshape(-1, 1))
lr9.fit(XG3[:, 2].reshape(-1, 1), YG3_true[:, 2].reshape(-1, 1))
'''

#まさかとは思うがXとYを逆にしてみる
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

'''
#テストデータでマトリクスを作る場合
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

lr.fit(x4.reshape(-1, 1), c1x.reshape(-1, 1))
lr2.fit(x4.reshape(-1, 1), c2x.reshape(-1, 1))
lr3.fit(x4.reshape(-1, 1), c3x.reshape(-1, 1))

lr4.fit(x5.reshape(-1, 1), c1y.reshape(-1, 1))
lr5.fit(x5.reshape(-1, 1), c2y.reshape(-1, 1))
lr6.fit(x5.reshape(-1, 1), c3y.reshape(-1, 1))

lr7.fit(x6.reshape(-1, 1), c1z.reshape(-1, 1))
lr8.fit(x6.reshape(-1, 1), c2z.reshape(-1, 1))
lr9.fit(x6.reshape(-1, 1), c3z.reshape(-1, 1))
'''

#print(XG)
#print(YG_true)


matrix = np.array([[lr.coef_[0, 0], lr4.coef_[0, 0], lr7.coef_[0, 0]],
                    [lr2.coef_[0, 0], lr5.coef_[0, 0], lr8.coef_[0, 0]], 
                    [lr3.coef_[0, 0], lr6.coef_[0, 0], lr9.coef_[0, 0]]])

'''
matrix = np.array([[lr7.coef_[0, 0], lr8.coef_[0, 0], lr9.coef_[0, 0]],
                    [lr4.coef_[0, 0], lr5.coef_[0, 0], lr6.coef_[0, 0]], 
                    [lr.coef_[0, 0], lr2.coef_[0, 0], lr3.coef_[0, 0]]])
'''
print(matrix)
inv_matrix = np.linalg.inv(matrix)

'''
inv_matrix = np.array([[2, 0, 0],
                    [0, 2, 0], 
                    [0, 0, 2]])

'''

#print(matrix)
print(inv_matrix)
#print(np.dot(matrix, inv_matrix))
#力技でテストデータの変換
XG4_pred = XG4.T
# print(XG4_pred.shape[1])


for i in range(XG4_pred.shape[1]):
    XG4_pred[:, i] = np.dot(inv_matrix, XG4_pred[:, i])
#print(XG3)
XG4_pred = XG4_pred.T

#print(XG4_pred)

ax3.scatter(YG4_true[::500, 2], XG4_pred[::500, 2])
#ax3.plot(timec, XG4_pred[:, 2])
ax3.set_xlim([-0.5, 2.5])
ax3.set_ylim([-1.0, 1.5])
ax3.grid()
ax3.set_ylabel("Calculated Load (N)")
ax3.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-5, 50, 1) #基準線表示(y=x)
height = np.arange(-5, 50, 1)
ax3.plot(left, height, linestyle="dashed", color="red")
ax3.set_title("preddata_Pressure")

xt = (YG4_true[::500, 0]) #x軸点の数
xp = XG4_pred[::500, 0]
yt = 1 *(YG4_true[::500, 1]) #y軸
yp =1 *  XG4_pred[::500, 1]

ax4.scatter(xt, xp, s=5)
ax4.scatter(yt, yp, s=5)

ax4.set_xlim([-0.4, 0.1])
ax4.set_ylim([-0.5, 0.2])
ax4.grid()
ax4.legend(["X_Shear_force","Y_Shear_force"])
ax4.set_ylabel("Calculated Load (N)")
ax4.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-10, 10, 1) #基準線表示(y=x)
height = np.arange(-10, 10, 1)
ax4.plot(left, height, linestyle="dashed", color="red")
ax4.set_title("preddata_Shear force")

plt.show()


#print('matrix = ', matrix) # 説明変数の係数を出力
#print('intercept = ', lr.intercept_) # 切片を出力
#print('score = ', lr.score(XG, YG_true))#決定係数を出力



'''
Y_pred = lr.predict(XG[:, 0].reshape(-1, 1)) # 学習データに対する目的変数を予測
Y2_pred = lr2.predict(XG[:, 1].reshape(-1, 1))
Y3_pred = lr3.predict(XG[:, 2].reshape(-1, 1))
Y4_pred = lr4.predict(XG2[:, 0].reshape(-1, 1))
Y5_pred = lr5.predict(XG2[:, 1].reshape(-1, 1))
Y6_pred = lr6.predict(XG2[:, 2].reshape(-1, 1))
Y7_pred = lr7.predict(XG3[:, 0].reshape(-1, 1))
Y8_pred = lr8.predict(XG3[:, 1].reshape(-1, 1))
Y9_pred = lr9.predict(XG3[:, 2].reshape(-1, 1))


#print('RMSE all train data: ', np.sqrt(mean_squared_error(YG_true, Y_pred))) #平方根をとったもの
#print('RMSE x train data: ', np.sqrt(mean_squared_error(x4, Y_pred[:, 0])))
#print('RMSE y train data: ', np.sqrt(mean_squared_error(x5, Y_pred[:, 1])))
#print('RMSE z train data: ', np.sqrt(mean_squared_error(x6, Y_pred[:, 2])))

#print('RMSE test1 train data: ', np.sqrt(mean_squared_error([10,20], [10,10])))
#print('RMSE test2 train data: ', np.sqrt(mean_squared_error([10,20], [10,50])))

#print(Y_pred)
#print(Y_pred[:, 0])

#学習データ比較(剪断X)
y1c1 = (YG_true[::100, 0]) #0から1000までのデータの中で10個おきにデータをとる
y1c1_pred = Y_pred[::100 , 0] #学習した出力データ

y1c2 = (YG_true[::100, 1]) #0から1000までのデータの中で10個おきにデータをとる
y1c2_pred = Y2_pred[::100 , 0] #学習した出力データ

y1c3 = (YG_true[::100, 2]) #0から1000までのデータの中で10個おきにデータをとる
y1c3_pred = Y3_pred[::100 , 0] #学習した出力データ

#print('y1shape = ', y1.shape) #サンプル長確認
#print('y1_predshape = ', y1_pred.shape)

#ax3.scatter(y1, y_pred, s=5)
ax1.plot(y1c1, y1c1_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
#ax3.set_xlim([-0.5, 6])
#ax3.set_ylim([-0.5, 6])
ax1.grid()
#ax3.set_ylabel("Calculated Load (N)")
#ax3.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-5, 50, 1) #基準線表示(y=x)
height = np.arange(-5, 50, 1)
ax1.plot(left, height, linestyle="dashed", color="red")
#ax3.set_title("preddata_Pressure")

ax2.plot(y1c2, y1c2_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax2.grid()
ax2.plot(left, height, linestyle="dashed", color="red")

ax3.plot(y1c3, y1c3_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax3.grid()
ax3.plot(left, height, linestyle="dashed", color="red")


#学習データ比較(剪断Y)
y2c1 = (YG2_true[::100, 0]) #0から1000までのデータの中で10個おきにデータをとる
y2c1_pred = Y4_pred[::100 , 0] #学習した出力データ

y2c2 = (YG2_true[::100, 1]) #0から1000までのデータの中で10個おきにデータをとる
y2c2_pred = Y5_pred[::100 , 0] #学習した出力データ

y2c3 = (YG2_true[::100, 2]) #0から1000までのデータの中で10個おきにデータをとる
y2c3_pred = Y6_pred[::100 , 0] #学習した出力データ

#print('y1shape = ', y1.shape) #サンプル長確認
#print('y1_predshape = ', y1_pred.shape)

#ax3.scatter(y1, y_pred, s=5)
ax4.plot(y2c1, y2c1_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
#ax3.set_xlim([-0.5, 6])
#ax3.set_ylim([-0.5, 6])
ax4.grid()
#ax3.set_ylabel("Calculated Load (N)")
#ax3.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-5, 50, 1) #基準線表示(y=x)
height = np.arange(-5, 50, 1)
ax4.plot(left, height, linestyle="dashed", color="red")
#ax3.set_title("preddata_Pressure")

ax5.plot(y2c2, y2c2_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax5.grid()
ax5.plot(left, height, linestyle="dashed", color="red")

ax6.plot(y2c3, y2c3_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax6.grid()
ax6.plot(left, height, linestyle="dashed", color="red")


#学習データ比較(圧力Z)
y3c1 = (YG3_true[::100, 0]) #0から1000までのデータの中で10個おきにデータをとる
y3c1_pred = Y7_pred[::100 , 0] #学習した出力データ

y3c2 = (YG3_true[::100, 1]) #0から1000までのデータの中で10個おきにデータをとる
y3c2_pred = Y8_pred[::100 , 0] #学習した出力データ

y3c3 = (YG3_true[::100, 2]) #0から1000までのデータの中で10個おきにデータをとる
y3c3_pred = Y9_pred[::100 , 0] #学習した出力データ

#print('y1shape = ', y1.shape) #サンプル長確認
#print('y1_predshape = ', y1_pred.shape)

#ax3.scatter(y1, y_pred, s=5)
ax7.plot(y3c1, y3c1_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
#ax3.set_xlim([-0.5, 6])
#ax3.set_ylim([-0.5, 6])
ax7.grid()
#ax3.set_ylabel("Calculated Load (N)")
#ax3.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-5, 50, 1) #基準線表示(y=x)
height = np.arange(-5, 50, 1)
ax7.plot(left, height, linestyle="dashed", color="red")
#ax3.set_title("preddata_Pressure")

ax8.plot(y3c2, y3c2_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax8.grid()
ax8.plot(left, height, linestyle="dashed", color="red")

ax9.plot(y3c3, y3c3_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
ax9.grid()
ax9.plot(left, height, linestyle="dashed", color="red")

plt.show()

#学習データ比較(せん断力)

y2 = (YG_true[::100, 0]) #x軸点の数
y2_pred = Y_pred[::100, 0]
y3 = 1 *(YG_true[::100, 1]) #y軸
y3_pred =1 *  Y_pred[::100, 1]

print('y3shape = ', y3.shape)
print('y3shape = ', y3.shape)

ax4.scatter(y2, y2_pred, s=5)
ax4.scatter(y3, y3_pred, s=5)

#ax4.plot(y2, y2_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)
#ax4.plot(y3, y3_pred, linewidth=1, marker="o", markersize=5, markeredgewidth=0)

ax4.set_xlim([-1.0, 1.0])
ax4.set_ylim([-1.0, 1.0])
ax4.grid()
ax4.legend(["X_Shear_force","Y_Shear_force"])
ax4.set_ylabel("Calculated Load (N)")
ax4.set_xlabel("Measurement of Loadcel (N)")

left = np.arange(-10, 10, 1) #基準線表示(y=x)
height = np.arange(-10, 10, 1)
ax4.plot(left, height, linestyle="dashed", color="red")
ax4.set_title("preddata_Shear force")

plt.show()
'''

#時系列、圧力、剪断プロット
timec2 = np.arange(XG4_pred[:, 2].shape[0])
timec2 = timec2 / 2000

fig2 = plt.figure(figsize=(10,7)) #グラフ表示の枠を調節
fig2.subplots_adjust(hspace=0.3, wspace=0.2) #グラフ間の距離を調節
ax5 = fig2.add_subplot(2, 2, 1) #グラフの分割表示
ax6 = fig2.add_subplot(2, 2, 2)
ax7 = fig2.add_subplot(2, 2, 3)
ax8 = fig2.add_subplot(2, 2, 4)


ax5.plot(timec2, x6)
ax5.plot(timec2, XG4_pred[:, 2])

ax5.set_title("roadcell_pred Time series")
ax5.legend(["roadcell_pressure","predict_data"])
ax5.set_ylabel("Change of Loadcel (N)")
ax5.set_xlabel("Time (sec)")
#ax5.set_xlim([0, 40])
ax5.grid()

#剪断X
timec2 = np.arange(XG4_pred[:, 0].shape[0])
timec2 = timec2 / 2000

ax6.plot(timec2, x4)
ax6.plot(timec2, XG4_pred[:, 0])

ax6.set_title("roadcell_pred Time series")
ax6.legend(["roadcell_shareforceX","predict_data"])
ax6.set_ylabel("Change of Loadcel (N)")
ax6.set_xlabel("Time (sec)")
#ax6.set_xlim([0, 40])
ax6.grid()

#剪断Y
timec2 = np.arange(XG4_pred[:, 1].shape[0])
timec2 = timec2 / 2000

ax7.plot(timec2, x5)
ax7.plot(timec2, XG4_pred[:, 1])

ax7.set_title("roadcell_pred Time series")
ax7.legend(["roadcell_shareforceY","predict_data"])
ax7.set_ylabel("Change of Loadcel (N)")
ax7.set_xlabel("Time (sec)")
#ax7.set_xlim([0, 40])
ax7.grid()

ax8.set_title("matrix")
ax8.text(0.1, 0.5, inv_matrix, size = 10)
ax8.axis("off")

plt.show()
