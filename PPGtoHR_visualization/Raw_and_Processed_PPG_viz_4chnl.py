# Script to Visualize Raw and Processed Verisense PPG Data
# by mpatterson@shimmersensing.com
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.backends.backend_pdf
import matplotlib.dates as mdates
import math
from numpy.fft import fft, fftshift
from scipy import signal

header_size = 11
sampling_rate = 50
remove_avg = True
apply_lpf = True

ch_colour_ref = {
    "PPG_Red": 'red',
    "PPG_IR": 'purple',
    "PPG_Green": 'green',
    "PPG_Blue": 'blue'
}

# raw_data_folder = "C:/Users/Mark/Downloads/2020-10-14 PPG/NamanPPG/200929018D8F/ParsedFiles"
# processed_data_folder = "C:/Users/Mark/Downloads/2020-10-14 PPG/NamanPPG/Algorithms/PPGtoHR"


# https://tomroelandts.com/articles/how-to-create-a-simple-low-pass-filter
def create_lp_filter():
    fc = 5 / sampling_rate  # Cutoff frequency as a fraction of the sampling rate (in (0, 0.5)).
    # b = 0.08  # Transition band, as a fraction of the sampling rate (in (0, 0.5)).
    b = 0.02  # equates to N = 200 as per our Java implementation
    N = int(np.ceil((4 / b)))
    if not N % 2: N += 1  # Make sure that N is odd.
    n = np.arange(N)

    # Compute sinc filter.
    # h = np.sinc(2 * fc * (n - (N - 1) / 2))
    sinc_func = np.sinc(2 * fc * (n - (N - 1) / 2.))

    # Compute Blackman window.
    # window = 0.42 - 0.5 * np.cos(2 * np.pi * n / (N - 1)) + \
    #     0.08 * np.cos(4 * np.pi * n / (N - 1))
    window = np.blackman(N)

    # Multiply sinc filter by window.
    # h = h * w
    sinc_func = sinc_func * window

    # Normalize to get unity gain.
    # h = h / np.sum(h)
    sinc_func = sinc_func / np.sum(sinc_func)

    # plt.plot(window)
    # plt.title("Blackman window")
    # # Text(0.5, 1.0, 'Blackman window')
    # plt.ylabel("Amplitude")
    # # Text(0, 0.5, 'Amplitude')
    # plt.xlabel("Sample")
    # # Text(0.5, 0, 'Sample')
    # plt.show()

    # # Plot the frequency response
    # # https://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.signal.freqz.html
    # plot_freq = True
    # w, h = signal.freqz(sinc_func)
    # if plot_freq:
    #     w = w * 2 * math.pi
    # fig, (ax1) = plt.subplots(1, 1)
    # plt.title('Digital filter frequency response')
    # plt.plot(w, 20 * np.log10(abs(h)), 'b')
    # plt.ylabel('Amplitude [dB]', color='b')
    # if plot_freq:
    #     plt.xlabel('Frequency [Hz]')
    # else:
    #     plt.xlabel('Frequency [rad/sample]')
    # ax2 = ax1.twinx()
    # angles = np.unwrap(np.angle(h))
    # plt.plot(w, angles, 'g')
    # plt.ylabel('Angle (radians)', color='g')
    # plt.grid()
    # plt.axis('tight')
    # plt.show()

    return sinc_func


if __name__ == "__main__":

    verbose = True

    if verbose:
        print("Raw and Processed Verisense PPG Visualization Tool v0.00.001")

    if "raw_data_folder" not in globals():
        print('RAW Files Location (use fwd slashes):')
        raw_data_folder = input("Folder: ")
    if raw_data_folder[-1] != "/":
        raw_data_folder = raw_data_folder + "/"
    if "processed_data_folder" not in globals():
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
    hr_coverage = []
    hr_mean = []

    if apply_lpf:
        sinc_func = create_lp_filter()

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
                df_hr = pd.read_csv(processed_data_folder+processed_file_name,skiprows=header_size,names=['UNIX_ms','HR_bpm','IBI_ms'])
                df_hr['TimeStamp'] = [datetime.utcfromtimestamp(x/1000) for x in df_hr.UNIX_ms]
                df_raw = pd.read_csv(raw_data_folder+x,skiprows=[0,1,2,3,4,5,6,7,8,10])

                ppg_max = 0
                ppg_min = 0

                # If LPF enabled, skip 10 seconds for filter settling time. Else, skip two FIFO buffers to allow time for proximity detection in the FW.
                samples_to_skip = (15 * sampling_rate) if apply_lpf else (2*17)
                samples_to_skip_end = samples_to_skip+(45*sampling_rate)

                for col_name, ppg_ch in df_raw.items():
                    # Applying the filter h to a signal s
                    if apply_lpf:
                        ppg_ch = pd.Series(np.convolve(ppg_ch, sinc_func))

                    ppg_ch_sliced = ppg_ch.iloc[samples_to_skip:samples_to_skip_end]
                    # ppg_ch_sliced = ppg_ch.iloc[samples_to_skip:]

                    # Subtract the avg from each signal
                    if remove_avg:
                        ppg_ch = ppg_ch - ppg_ch_sliced.mean()

                    ppg_max = max(ppg_max, ppg_ch.iloc[samples_to_skip:samples_to_skip_end].max())
                    ppg_min = min(ppg_min, ppg_ch.iloc[samples_to_skip:samples_to_skip_end].min())

                    df_raw[col_name] = ppg_ch

                # print("max = ", ppg_max, ", Min = ", ppg_min)

                df = pd.concat([df_hr, df_raw],axis=1)
                # plot
                ax1 = fig1.add_subplot(4,1,i+1)

                the_year = df.TimeStamp[1].year
                the_month = df.TimeStamp[1].month
                the_day = df.TimeStamp[1].day
                ax1.set_title(str(the_year)+'-'+str(the_month)+'-'+str(the_day)+' [Y-M-D]')
                ax1.grid()
                ax1.set_ylabel('PPG-raw')
                #ax1.plot(df.TimeStamp,df.PPG,label='PPG-raw')

                for col_name, ppg_ch in df_raw.items():
                    ax1.plot(df.TimeStamp, ppg_ch, label=col_name, color=ch_colour_ref[col_name])

                ax1.set_ylim(ppg_min-0.01,ppg_max+0.01)
                ax1.legend(loc=2)
                ax2 = ax1.twinx()
                ax2.set_ylabel('HR [bpm]')
                ax2.plot(df.TimeStamp,df.HR_bpm,color='orange',label='HR',alpha=0.8)
                ax2.legend(loc=1)
                count_artefact = (df['HR_bpm']==-1).sum()
                hr_cov = 1 - (count_artefact / len(df.HR_bpm))
                hr_cov = hr_cov * 100
                hr_coverage.append(hr_cov)
                y_lims = ax1.get_ylim()
                y_lev = y_lims[0]+((y_lims[1]-y_lims[0])*0.9)
                x_lims = ax1.get_xlim()
                x_quarter = (x_lims[1]-x_lims[0]) / 4
                ax1.text(x_lims[0]+x_quarter,y_lev,'HR Coverage [%]: '+str(round(hr_cov,2)),fontweight='bold')
                # what is the avg HR in good data?
                if hr_cov == 0:
                    hr_mean.append(0)
                    ax1.text(x_lims[0]+(2*x_quarter),y_lev,'Error: No Measured HR',fontweight='bold')
                else:
                    good_hr = df['HR_bpm'] > -1
                    df_hr = df[good_hr]
                    mean_hr = df_hr.HR_bpm.mean()
                    hr_mean.append(mean_hr)
                    ax1.text(x_lims[0]+(2*x_quarter),y_lev,'Mean HR [bpm]: '+str(round(mean_hr,2)),fontweight='bold')

				# Uncomment for quicker debugging of graphs
                # plt.show()


            else:
                print('Error: No associated processed HR file to match raw PPG file: '+x) # print file name
        plt.tight_layout()
        pdf.savefig(fig1)
        if verbose:
            print('Writing Plot Page # '+str(i_pg+1))
    pdf.close()
    dict = {'FileName': raw_files_list, 'HR-mean-bpm': hr_mean, 'HR-Coverage-%': hr_coverage}
    df2 = pd.DataFrame(dict)
    print('Writing csv report')
    df2.to_csv(raw_data_folder+'summary_report'+current_time+'.csv')
