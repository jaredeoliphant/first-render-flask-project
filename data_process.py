import pandas as pd
import numpy as np
from scipy.signal import correlate,find_peaks




def data_process(filename):
    
    ## output file with suffix added as well as a log file for storing speed calculation
    # outputfilename = filename.split('.csv')[0] + '_OFFSET'
    # logfilename = filename.split('.csv')[0] + '_log.txt'
    
    ## read the csv file in first to just get the testID,sampleRate,and channel information
    headerdata = pd.read_csv(filename)
    # headerdata = pd.read_csv('298-064_FILTERED.csv')
    
    ## clean up
    headerdata.dropna(axis=1,how='all',inplace=True)
    header = headerdata.iloc[:21]
    
    ## extract useful data
    testID = headerdata.iloc[2][1]
    sampleRate = int(headerdata.iloc[4][1])
    channels = headerdata.iloc[8][1:8]
    
    ## read in the csv file again with only the meat of the data after the header section
    data = pd.read_csv(filename,skiprows=22) 
    
    ## clean up
    data.drop('Unnamed: 8',inplace=True,axis=1) 
    
    
    ## sort the columns as needed to get them into the following order:
    ## X accel, Y accel, Z accel, Roll, Pitch, Yaw
    channel_list = headerdata.iloc[8][1:] ## channel descriptions [0,4,5,6,1,2,3]
    current_columns = data.columns.to_list()
    cur_columns_header = header.columns.to_list()
    
    sortindex = []
    for channel in channel_list:
        if 'Speed' in channel:
            sortindex.append(0)
        if 'Long' in channel:
            sortindex.append(1)
        if 'Lat' in channel:
            sortindex.append(2)
        if 'Vert' in channel:
            sortindex.append(3)
        if 'Roll' in channel:
            sortindex.append(4)
        if 'Pitch' in channel:
            sortindex.append(5)
        if 'Yaw' in channel:
            sortindex.append(6)
        
    new_columns = ['Time']
    new_header_col = ['Headers']
    for x in range(7):
        new_columns.append(current_columns[1+sortindex[x]])
        new_header_col.append(cur_columns_header[1+sortindex[x]])
        # print(x,new_columns,new_header_col)
    
    ## use the new column list to reorder (reindex) the header dataframe and the data dataframe
    data = data.reindex(columns=new_columns)
    header = header.reindex(columns=new_header_col)
    
    
    endd = 16750
    time_arr = data['Time'].iloc[0:endd].to_numpy()
    speed_arr = data['Chan 0:SPEED SENSOR'].iloc[0:endd].to_numpy()
    factor = 15
    resampled_time, resampled_arr = resample_signal(time_arr, speed_arr, factor=factor)
    
    peaks, therest = find_peaks(-abs(resampled_arr+100),prominence=35)
    speed_leading = factor*30008*3600/1000/(peaks[2]-peaks[0])
    offset = 3.6/speed_leading
    

    ## plot raw speed sensor data for user to confirm nothing is fishy
    
    xlim_param = resampled_time[peaks[0]] - 0.03275 + .03+.0017
    
    
    return {'speed_kmh':speed_leading,
            'xlim_param':xlim_param,
            'offset':offset,
            'testID':testID,
            'sampleRate':sampleRate
            }

def resample_signal(t_arr,x_arr,factor=2):

    length = len(t_arr)
    idx = pd.date_range("2018-01-01", periods=length, freq="H")
    ts = pd.DataFrame(pd.Series(t_arr, index=idx,name='time'))
    ts['signal'] = x_arr
    
    minutes = 60/factor
    resampled = ts.resample('{0}Min'.format(int(minutes))).first().interpolate(method='polynomial',order=1)
    return resampled['time'].to_numpy(), resampled['signal'].to_numpy()

