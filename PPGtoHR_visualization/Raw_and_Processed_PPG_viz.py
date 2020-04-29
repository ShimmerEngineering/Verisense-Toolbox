# Script to Visualize Raw and Processed Verisense PPG Data
# by mpatterson@shimmersensing.com
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import pathlib as Path
import matplotlib.backends.backend_pdf
import matplotlib.dates as mdates
import math
#


if __name__ == "__main__":

    verbose = True

    if verbose:
        print("Raw and Processed Verisense PPG Visualization Tool v0.00.001")
    print('RAW Files Location (use fwd slashes):')
    raw_data_folder = input("Folder: ")
    if raw_data_folder[-1] != "/":
        raw_data_folder = raw_data_folder + "/"
    print('PROCESSED Files Location (use fwd slashes):')
    processed_data_folder = input("Folder: ")
    if processed_data_folder[-1] != "/":
        processed_data_folder = processed_data_folder + "/"
    raw_files_list = os.listdir(raw_data_folder)
    raw_files_list = [x for x in raw_files_list if x[14:17] == 'PPG']
    if not raw_files_list:
        print('Error: No processed files found in that folder')
    now = datetime.now()
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    pdf = matplotlib.backends.backend_pdf.PdfPages(raw_data_folder + 'PPGtoHR_check_raw_' + current_time + '.pdf')
    num_pgs = math.ceil(len(raw_files_list)/4)
    file_count = 0

    for i_pg in np.arange(num_pgs):
        fig1=plt.figure(figsize=(10,10))
        for i in np.arange(4):
            if file_count >= len(raw_files_list):
                break
            x = raw_files_list[file_count]
            file_count = file_count + 1
            file_dt = x[0:13]  # create file name for processed file
            file_num = x[22:27]
            processed_file_name = file_dt + '_PPGtoHR_' + file_num + '.csv'
            if os.path.isfile(processed_data_folder + processed_file_name):
                df_hr = pd.read_csv(processed_data_folder+processed_file_name,skiprows=12,names=['UNIX_ms','HR_bpm','IBI_ms'])
                df_hr['TimeStamp'] = [datetime.fromtimestamp(x/1000) for x in df_hr.UNIX_ms]
                df_raw = pd.read_csv(raw_data_folder+x,skiprows=12,names=['PPG'])
                df = pd.concat([df_hr, df_raw],axis=1)
                # plot
                ax1 = fig1.add_subplot(4,1,i+1)
                ppg_max = df.PPG[1:len(df.PPG)].max()
                ppg_min = df.PPG[1:len(df.PPG)].min()
                the_year = df.TimeStamp[1].year
                the_month = df.TimeStamp[1].month
                the_day = df.TimeStamp[1].day
                ax1.set_title(str(the_year)+'-'+str(the_month)+'-'+str(the_day)+' [Y-M-D]')
                ax1.grid()
                ax1.set_ylabel('PPG-raw')
                ax1.plot(df.TimeStamp,df.PPG,label='PPG-raw')
                ax1.set_ylim(ppg_min-0.01,ppg_max+0.01)
                ax1.legend(loc=2)
                ax2 = ax1.twinx()
                ax2.set_ylabel('HR [bpm]')
                ax2.plot(df.TimeStamp,df.HR_bpm,color='red',label='HR')
                ax2.legend()
            else:
                print('Error: No associated processed HR file to match raw PPG file: '+x) # print file name
        plt.tight_layout()
        pdf.savefig(fig1)
        if verbose:
            print('Writing Plot Page # '+str(i_pg+1))
    pdf.close()
