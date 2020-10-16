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
import boto3
import pytz
import time
import io
from pathlib import Path
from PPGtoHR_visualization import Verisense_Trial_Details

header_size = 11
sampling_rate = 50
remove_avg = True
apply_lpf = True
load_from_s3 = True

verisense_trial = None
s3_client = None

ch_colour_ref = {
    "PPG_Red": 'red',
    "PPG_IR": 'purple',
    "PPG_Green": 'green',
    "PPG_Blue": 'blue'
}


def get_file_lists_from_s3(verisense_trial, participant_id):
    global s3_client

    parsed_files_list = []
    ppgtohr_files_list = []

    my_session = boto3.Session(aws_access_key_id=verisense_trial.aws_access_key_id,
                               aws_secret_access_key=verisense_trial.aws_secret_access_key, region_name=verisense_trial.region_name)
    s3_client = my_session.client('s3')

    kwargs = {'Bucket': verisense_trial.bucketname, 'Prefix': (str(verisense_trial.trial_id) + '/' + participant_id + '/')}
    while True:
        resp = s3_client.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            key = obj['Key']
            if key.endswith(".csv"):
                obj['FileName'] = key[key.rindex('/') + 1:]
                if "PPG_CAL" in key:
                    parsed_files_list.append(obj)
                elif "PPGtoHR" in key:
                    ppgtohr_files_list.append(obj)
                # print(key)

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

    return parsed_files_list, ppgtohr_files_list


def get_file_lists_from_local_path(participant_path):
    result = list(Path(participant_path).rglob("*.[cC][sS][vV]"))

    parsed_files_list = [fileObj for fileObj in result if "PPG_CAL" in fileObj.name]
    if not parsed_files_list:
        print('Error: No processed files found in that folder')
    ppgtohr_files_list = [fileObj for fileObj in result if "PPGtoHR" in fileObj.name]

    return parsed_files_list, ppgtohr_files_list


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

    # plot_filter_window(window)
    # plot_filter_freq_response(sinc_func)

    return sinc_func


def plot_filter_window(window):
    plt.plot(window)
    plt.title("Blackman window")
    # Text(0.5, 1.0, 'Blackman window')
    plt.ylabel("Amplitude")
    # Text(0, 0.5, 'Amplitude')
    plt.xlabel("Sample")
    # Text(0.5, 0, 'Sample')
    plt.show()


def plot_filter_freq_response(z):
    # Plot the frequency response
    # https://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.signal.freqz.html
    plot_freq = True
    w, h = signal.freqz(z)
    if plot_freq:
        w = w * 2 * math.pi
    fig, (ax1) = plt.subplots(1, 1)
    plt.title('Digital filter frequency response')
    plt.plot(w, 20 * np.log10(abs(h)), 'b')
    plt.ylabel('Amplitude [dB]', color='b')
    if plot_freq:
        plt.xlabel('Frequency [Hz]')
    else:
        plt.xlabel('Frequency [rad/sample]')
    ax2 = ax1.twinx()
    angles = np.unwrap(np.angle(h))
    plt.plot(w, angles, 'g')
    plt.ylabel('Angle (radians)', color='g')
    plt.grid()
    plt.axis('tight')
    plt.show()


def determine(x, date_start, date_end):
    if isinstance(x, dict):
        file_name = x['FileName']
    else:
        file_name = x.name

    date_string = file_name[0:13]
    ts = datetime.strptime(date_string, "%y%m%d_%H%M%S")
    ts = pytz.UTC.localize(ts)

    if date_start <= ts <= date_end:
        return True
    else:
        return False


if __name__ == "__main__":

    verbose = True

    if verbose:
        print("Raw and Processed Verisense PPG Visualization Tool v0.00.001")

    datestart = datetime(2020, 10, 14, 11, 6, 0, 0, pytz.UTC)
    dateend = datetime(2020, 10, 15, 0, 0, 0, 0, pytz.UTC)

    if load_from_s3:
        participant_id = "NamanPPG"
        verisense_trial = Verisense_Trial_Details.DublinDD
        # # participant_id = ""
        # verisense_trial = None

        if not participant_id:
            participant_id = input("Participant ID: ")
        if not verisense_trial:
            verisense_trial_name = input("Trial Name: ")
            if "Dublin" in verisense_trial_name:
                verisense_trial = Verisense_Trial_Details.DublinDD

        print("Searching S3 for Participant: ", participant_id)
        parsed_files_list, ppgtohr_files_list = get_file_lists_from_s3(verisense_trial, participant_id)
        output_results_path = str(Path(__file__).parent.absolute()) + "/"
    else:
        # participant_path = "C:/Users/Mark/Downloads/2020-10-14 PPG/NamanPPG"
        participant_path = ""

        if not participant_path:
            print('Participant Path (use fwd slashes):')
            participant_path = input("Folder: ")

        if participant_path[-1] != "/":
            participant_path += "/"

        print("Loading from local path: ")
        parsed_files_list, ppgtohr_files_list = get_file_lists_from_local_path(participant_path)
        output_results_path = participant_path

    output_results_path += "Output/"
    if not os.path.exists(output_results_path):
        os.makedirs(output_results_path)

    print("Filtering for Start Date: ", datestart, ", End Date: ", dateend)
    parsed_files_list = [fileObj for fileObj in parsed_files_list if determine(fileObj, datestart, dateend)]
    ppgtohr_files_list = [fileObj for fileObj in ppgtohr_files_list if determine(fileObj, datestart, dateend)]

    now = datetime.now()
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    pdf = matplotlib.backends.backend_pdf.PdfPages(output_results_path + 'PPGtoHR_check_raw_' + current_time + '.pdf')
    num_pgs = math.ceil(len(parsed_files_list) / 4)
    file_count = 0
    hr_coverage = []
    hr_mean = []

    if apply_lpf:
        sinc_func = create_lp_filter()

    for i_pg in np.arange(num_pgs):
        fig1 = plt.figure(figsize=(10, 10))
        for i in np.arange(4):
            if file_count >= len(parsed_files_list):
                break
            parsed_file = parsed_files_list[file_count]
            file_count += 1
            if s3_client is not None:
                parsed_file_name = parsed_file['FileName']
            else:
                parsed_file_name = parsed_file.name
            file_dt = parsed_file_name[0:13]  # create file name for processed file
            file_num = parsed_file_name[22:27]

            processed_file_name = file_dt + '_PPGtoHR_' + file_num + '.csv'
            # if os.path.isfile(processed_data_folder + processed_file_name):

            if s3_client is not None:
                processed_file = next((item for item in ppgtohr_files_list if item["FileName"] == processed_file_name), None)
            else:
                processed_file = next((item for item in ppgtohr_files_list if item.name == processed_file_name), None)

            if processed_file is not None:
                if s3_client is not None:
                    # https://stackoverflow.com/questions/37703634/how-to-import-a-text-file-on-aws-s3-into-pandas-without-writing-to-disk
                    obj = s3_client.get_object(Bucket=verisense_trial.bucketname, Key=processed_file['Key'])
                    processed_file_stream = io.BytesIO(obj['Body'].read())
                    obj = s3_client.get_object(Bucket=verisense_trial.bucketname, Key=parsed_file['Key'])
                    parsed_file_stream = io.BytesIO(obj['Body'].read())
                else:
                    processed_file_stream = processed_file
                    parsed_file_stream = parsed_file

                df_hr = pd.read_csv(processed_file_stream, skiprows=header_size, names=['UNIX_ms', 'HR_bpm', 'IBI_ms'])
                df_hr['TimeStamp'] = [datetime.utcfromtimestamp(x / 1000) for x in df_hr.UNIX_ms]
                # df_hr = pd.read_csv(processed_data_folder+processed_file_name,skiprows=[0,1,2,3,4,5,6,7,8,10])
                # df_hr['TimeStamp'] = [datetime.utcfromtimestamp(x/1000) for x in df_hr.Timestamp]

                df_raw = pd.read_csv(parsed_file_stream, skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 10])

                ppg_max = 0
                ppg_min = 0

                # If LPF enabled, skip 15 seconds for filter settling time. Else, skip two FIFO buffers to allow time for proximity detection in the FW.
                samples_to_skip = (15 * sampling_rate) if apply_lpf else (2 * 17)
                samples_to_skip_end = samples_to_skip + (45 * sampling_rate)

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

                df = pd.concat([df_hr, df_raw], axis=1)
                # plot
                ax1 = fig1.add_subplot(4, 1, i + 1)

                the_year = df.TimeStamp[1].year
                the_month = df.TimeStamp[1].month
                the_day = df.TimeStamp[1].day
                ax1.set_title(str(the_year) + '-' + str(the_month) + '-' + str(the_day) + ' [Y-M-D]')
                ax1.grid()
                ax1.set_ylabel('PPG-raw')
                # ax1.plot(df.TimeStamp,df.PPG,label='PPG-raw')

                for col_name, ppg_ch in df_raw.items():
                    ax1.plot(df.TimeStamp, ppg_ch, label=col_name, color=ch_colour_ref[col_name])

                ax1.set_ylim(ppg_min - 0.01, ppg_max + 0.01)
                ax1.legend(loc=2)
                ax2 = ax1.twinx()
                ax2.set_ylabel('HR [bpm]')
                ax2.plot(df.TimeStamp, df.HR_bpm, color='orange', label='HR', alpha=0.8)
                ax2.legend(loc=1)

                count_artefact = (df['HR_bpm'] == -1).sum()
                hr_cov = 1 - (count_artefact / len(df.HR_bpm))
                hr_cov = hr_cov * 100
                hr_coverage.append(hr_cov)

                y_lims = ax1.get_ylim()
                y_lev = y_lims[0] + ((y_lims[1] - y_lims[0]) * 0.9)
                x_lims = ax1.get_xlim()
                x_quarter = (x_lims[1] - x_lims[0]) / 4
                ax1.text(x_lims[0] + x_quarter, y_lev, 'HR Coverage [%]: ' + str(round(hr_cov, 2)), fontweight='bold')
                # what is the avg HR in good data?
                if hr_cov == 0:
                    hr_mean.append(0)
                    ax1.text(x_lims[0] + (2 * x_quarter), y_lev, 'Error: No Measured HR', fontweight='bold')
                else:
                    good_hr = df['HR_bpm'] > -1
                    df_hr = df[good_hr]
                    mean_hr = df_hr.HR_bpm.mean()
                    hr_mean.append(mean_hr)
                    ax1.text(x_lims[0] + (2 * x_quarter), y_lev, 'Mean HR [bpm]: ' + str(round(mean_hr, 2)),
                             fontweight='bold')

                # Uncomment for quicker debugging of graphs
                # plt.show()

            else:
                print('Error: No associated processed HR file to match raw PPG file: ' + parsed_file_name)  # print file name
        plt.tight_layout()
        pdf.savefig(fig1)
        if verbose:
            print('Writing Plot Page # ' + str(i_pg + 1))
    pdf.close()
    dict = {'FileName': parsed_files_list, 'HR-mean-bpm': hr_mean, 'HR-Coverage-%': hr_coverage}
    df2 = pd.DataFrame(dict)
    print('Writing csv report')
    df2.to_csv(output_results_path + 'summary_report' + current_time + '.csv')
