# Processed PPG visualization tool
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
        print("Processed Verisense PPG Visualization Tool v0.00.001")
    print('PROCESSED Files Location (use fwd slashes):')
    data_folder = input("Folder: ")
    if data_folder[-1] != "/":
        data_folder = data_folder + "/"
    print('Do you want to view HR [enter: 1] or IBI [enter: 0]?')
    isHR = input("HR_1_or_IBI_0: ")
    files_list = os.listdir(data_folder)
    # filter files list
    files_list = [x for x in files_list if x[14:21]=='PPGtoHR']
    if not files_list:
        print('Error: No processed files found in that folder')
    now = datetime.now()
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    if isHR:
        pdf = matplotlib.backends.backend_pdf.PdfPages(data_folder+'PPGtoHR_check_'+current_time+'.pdf')
    else:
        pdf = matplotlib.backends.backend_pdf.PdfPages(data_folder+'PPGtoIBI_check_'+current_time+'.pdf')
    num_pg = math.ceil(len(files_list)/16)
    file_count = 0
    is_artefact = []
    hr_coverage = []
    hr_mean = []

    for i_pg in np.arange(num_pg):
        print('Creating graphs on page '+str(i_pg+1)+' of '+str(num_pg+1))
        fig1=plt.figure(figsize=(10,10))
        for i in np.arange(16):
            if file_count >= len(files_list):
                break
            x = files_list[file_count]
            file_count = file_count + 1
            df_tmp = pd.read_csv(data_folder+x,skiprows=12,names=['UNIX_ms','HR_bpm','IBI_ms'])
            df_tmp['TimeStamp'] = [datetime.fromtimestamp(x/1000) for x in df_tmp.UNIX_ms]
            ax = fig1.add_subplot(4,4,i+1)
            if isHR:
                ax.plot(df_tmp.TimeStamp,df_tmp.HR_bpm,label='HR')
            else:
                ax.plot(df_tmp.TimeStamp,df_tmp.IBI_ms,color='red',label='IBI')#,linewidth=2,alpha=0.3)
            ax.grid()
            the_year = df_tmp.TimeStamp[1].year
            the_month = df_tmp.TimeStamp[1].month
            the_day = df_tmp.TimeStamp[1].day
            ax.set_title(str(the_year)+'-'+str(the_month)+'-'+str(the_day))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.xticks(rotation=45)
            if i % 4 == 0:
                if isHR:
                    ax.set_ylabel('HR [bpm]')
                else:
                    ax.set_ylabel('IBI [ms]')
            if i == 0:
                ax.legend()
            if df_tmp.HR_bpm.mean() == -1:
                is_artefact.append(1)
            else:
                is_artefact.append(0)
            count_artefact = (df_tmp['HR_bpm']==-1).sum()
            hr_cov = 1 - (count_artefact / len(df_tmp.HR_bpm))
            hr_coverage.append(hr_cov)
            # what is the avg HR in good data?
            if hr_cov == 0:
                hr_mean.append(0)
            else:
                good_hr = df_tmp['HR_bpm'] > -1
                df_hr = df_tmp[good_hr]
                hr_mean.append(df_hr.HR_bpm.mean())
        plt.tight_layout()
        pdf.savefig(fig1)
    pdf.close()

    dict = {'FileName': files_list, 'HR-mean': hr_mean, 'HR-Coverage-%': hr_coverage, 'Is Artefact': is_artefact}
    df2 = pd.DataFrame(dict)
    df2['HR-Coverage-%'] = df2['HR-Coverage-%'] * 100
    print('Writing csv report')
    df2.to_csv(data_folder+'summary_report'+current_time+'.csv')
