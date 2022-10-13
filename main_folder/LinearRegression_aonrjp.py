import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

from scipy import signal


legend_names=['Load-X','Load-Y','Load-Z','MEMS-ch1','MEMS-ch2','MEMS-ch3']
NI_SAMPLE_RATE = 2000

move_x_df = pd.read_csv('Nii_data/moving_X.csv', names=legend_names)
move_y_df = pd.read_csv('Nii_data/moving_Y.csv', names=legend_names)
move_z_df = pd.read_csv('Nii_data/moving_Z.csv', names=legend_names)
move_xyz_df = pd.read_csv('Nii_data/moving_XYZ.csv', names=legend_names)


# 計測データの確認
move_x_df.plot()
move_y_df.plot()
move_z_df.plot()
# move_xyz_df.plot()