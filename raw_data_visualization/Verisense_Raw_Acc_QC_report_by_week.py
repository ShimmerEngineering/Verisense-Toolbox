# Verisense Raw Accelerometer Data Quality Check Report
# 1 - enter the location of the raw ACCEL files in the 'folder to analyze'
# 2 - Cell / Run All: will run script and create pdf report in same folder
import numpy as np
import pandas as pd
import warnings
import collections
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
# %matplotlib inline


def pull_information(files_list):
    print('Opening up the next weeks files \n')
    dfByWeek = []
    dataByWeek = []
    startByWeek = []
    fileByWeek = []
    lenByWeek = []
    file_id = []
    raw_file_count = 0

    for x in files_list:
        if x[0:13] not in file_id:  # check that it's not a repeat
            raw_file_count += 1
            df_head = pd.read_csv(folder_to_analyze+x, nrows=7, names=('he'))
            if raw_file_count == 1:
                # parse out header data from the first file
                deviceName = df_head.h[0][16:29]
                deviceVersion = df_head.h[0][36:48]
                firmwareVersion = df_head.h[0][69:78]
                sample_rate = df_head.h[6][22:29]
                sensor_range = df_head.h[6][39:44]
                time = df_head.h[3][47:55]
                date = df_head.h[3][36:47]
                firstStart = date + " " + time
            time = df_head.h[3][47:55]
            date = df_head.h[3][36:47]
            startDate = pd.Timestamp(year=int(date[6:10]), month=int(date[3:5]), day=int(
                date[0:2]), hour=int(time[0:2]), minute=int(time[3:5]), second=int(time[6:8]))
            # file_start.append(startDate)
            startByWeek.append(startDate)
            # file_name.append(x)
            fileByWeek.append(x)
            file_id.append(x[0:13])
            df_tmp = pd.read_csv(folder_to_analyze+x,
                                 skiprows=12, names=['accX', 'accY', 'accZ'])
            df_tmp = df_tmp[acc_channel]  # keep only 1 channel for speed
            len_tmp = round((len(df_tmp)/(25*60*60)), 2)
            # file_len_hr.append(len_tmp)
            lenByWeek.append(len_tmp)
            dataByWeek.append(df_tmp)
            # file_data.append(df_tmp)
            try:
                frames = [dfByWeek, df_tmp]
                dfByWeek = pd.concat(frames)
            except:
                dfByWeek = df_tmp
        else:
            print('Ignored file', )
    return dfByWeek, dataByWeek, startByWeek, fileByWeek, lenByWeek, deviceName, deviceVersion, firmwareVersion, sample_rate, sensor_range, firstStart


def plot(file_name, df, file_start, file_len_hr, file_data, week, deviceName, deviceVersion, firmwareVersion, sample_rate, sensor_range, firstStart, duplicate_files, time_error_files):
    print('Processing the files \n')
    dict = {'File Name': file_name, 'Start Time': file_start,
            'File Length [hr]': file_len_hr}
    file_info = pd.DataFrame(dict)
    file_info.head()
    df.columns = [acc_channel]

    #
    describe = df.describe()
    naValues = df.isnull().sum()  # Check for N/A/null values
    # Replace all empty values with N/A
    df = df.replace(r'^\s*$', np.nan, regex=True)
    # Check for N/A's and subtract the original values to find the empty ones
    emptyValues = df.isnull().sum() - naValues
    uniqueValues = df.nunique()
    naEmpty = pd.DataFrame([uniqueValues, naValues, emptyValues], index=[
                           'Unique Values', 'N/A count', 'Empty count'])
    fullTable = describe.append(naEmpty)

    # Vertical table, without count, unique, n/a, and empty rounded to 0 decimals.
    fullTable = fullTable.T.round({"count": 0, "mean": 3, "std": 3, "min": 3, "25%": 3,
                                   "50%": 3, "75%": 3, "max": 3, "Unique Values": 3, "N/A count": 0, "Empty count": 0}).T
    fullTable

    # Importing the module and setting the pdf's title
    file_path = folder_to_analyze
    file_name_short = str(week)
    import matplotlib.backends.backend_pdf
    pdf = matplotlib.backends.backend_pdf.PdfPages(
        file_path + '/Verisense_Raw_Acc_QC/' + 'raw_acc_' + file_start[0].strftime("%m%d%Y") + "_to_" + file_start[-1].strftime("%m%d%Y") + '.pdf')

    #
    reportDate = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    firstPage = plt.figure(figsize=(12, 12))
    firstPage.clf()
    txt = 'Shimmer Verisense: Raw Acceleration Data Report\n\n Recording Start Date / Time: ' + firstStart + "\n Report Creation Date / Time: " + reportDate + '\n Date format: [d/m/y] \n\n Recorded by: ' + deviceName + " " + "\n Sensor ID: " + deviceVersion + "\n Firmare Version: " + firmwareVersion + \
        "\n Sample Rate: " + sample_rate + "\n Sensor Range: " + sensor_range + "\n Number of files: " + \
        str(len(dataByWeek)) + "\n Number of ignored duplicate files: " + str(len(duplicate_files)
                                                                              ) + "\n Number of ignored time error (1970) files: " + str(len(time_error_files))
    firstPage.text(0.5, 0.5, txt, transform=firstPage.transFigure,
                   size=24, ha="center")
    pdf.savefig()
    plt.close(firstPage)

    # Combination table of the describe function as well as the uniques, na, and empty columns.
    fig, ax = plt.subplots()
    ax.set_title('Accel Description Table')
    ax.axis('off')
    ax.table(cellText=fullTable.values, rowLabels=fullTable.index.values,
             colLabels=fullTable.columns, bbox=[0, 0, 1, 1])
    pdf.savefig(bbox_inches='tight')
    plt.close(fig)

    # plot file info table
    fig, ax = plt.subplots()
    ax.set_title('File Information Table')
    ax.axis('off')
    ax.table(cellText=file_info.values, rowLabels=file_info.index.values,
             colLabels=file_info.columns, bbox=[0, 0, 1, 1])
    pdf.savefig(bbox_inches='tight')
    plt.close(fig)

    # Histogram on one page
    fig = plt.figure(figsize=(10, 10))
    plt.hist(df, color='red', bins=50)
    plt.grid()
    plt.xlabel(acc_channel)
    plt.ylabel('counts')
    plt.title('Histogram of Raw Acceleration')

    pdf.savefig(fig)
    plt.close(fig)

    # Faster method of generating time stamps
    file_ts = []
    for idx, i_file in enumerate(file_data):
        file_ts.append(pd.date_range(
            file_start[idx], freq="40ms", periods=len(file_data[idx])))

    import matplotlib.dates as mdates

    # does the first element have a midnight in it?
    fs = 25 # this might be adaptable in the future..

    # is the first file longer than 1 day in samples?
    samples_per_day = fs*60*60*24

    fig1 = plt.figure(figsize=(10, 10))
    subplot_num = 0
    curr_day = 0
    y_font = 8 # y-label fontsize
    for idx, i_file in enumerate(file_data):
        start_day = file_ts[idx][0].day
        end_day = file_ts[idx][len(file_ts[idx])-1].day
        num_days = end_day - start_day + 1
        # figure out if a new subplot is required: compare start_day to curr_day
        if curr_day == start_day:
            new_day = False  # do not create a new subplot (same day as last one)
        else:
            new_day = True  # create new subplot
        if num_days > 1:
            start_idx = (file_ts[idx][0].hour * (fs*60*60)) + (file_ts[idx]
                                                               [0].minute * (fs*60)) + (file_ts[idx][0].second * fs)

        if num_days == 1:
            if new_day:
                if subplot_num == 7:
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 6)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 5)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 4)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 3)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 2)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 1)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax.set_xlabel('Time [hr]')
                    plt.tight_layout()
                    pdf.savefig(fig1)
                    subplot_num = 0
                subplot_num += 1
            ax = fig1.add_subplot(7, 1, subplot_num)
            ax.plot(file_ts[idx], i_file, color='red')
            ax.plot(file_ts[idx][0], 0, color='blue', marker='p')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            start_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 0, 0, 0)
            end_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 23, 59, 59) + pd.Timedelta(seconds=1)
            plt.xlim([start_datetime_xlim, end_datetime_xlim])
            plt.ylim([-50, 50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()
            curr_day = end_day

        elif num_days == 2:
            end_idx = samples_per_day - start_idx - 1
            if new_day:
                if subplot_num == 7:
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 6)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 5)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 4)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 3)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 2)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 1)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                    ax.set_xlabel('Time [hr]')
                    plt.tight_layout()
                    pdf.savefig(fig1)
                    subplot_num = 0
                subplot_num += 1
            ax = fig1.add_subplot(7, 1, subplot_num)
            ax.plot(file_ts[idx][0:end_idx], i_file[0:end_idx], color='red')
            ax.plot(file_ts[idx][0], 0, color='blue', marker='p')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            start_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 0, 0, 0)
            end_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 23, 59, 59) + pd.Timedelta(seconds=1)
            plt.xlim([start_datetime_xlim, end_datetime_xlim])
            plt.ylim([-50, 50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()

            # 2nd plot:
            end_idx += 1
            if subplot_num == 7:
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 6)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 5)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 4)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 3)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 2)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 1)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax.set_xlabel('Time [hr]')
                plt.tight_layout()
                pdf.savefig(fig1)
                subplot_num = 0

            subplot_num += 1
            ax = fig1.add_subplot(7, 1, subplot_num)
            ax.plot(file_ts[idx][end_idx:len(i_file)],
                    i_file[end_idx:len(i_file)], color='red')
            ax.plot(file_ts[idx][end_idx], 20, color='black', marker='o')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            start_datetime_xlim = end_datetime_xlim
            end_datetime_xlim = start_datetime_xlim + pd.Timedelta(hours=24)
            plt.xlim([start_datetime_xlim, end_datetime_xlim])
            plt.ylim([-50, 50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()
            curr_day = end_day

        # write final block of plots on final element
        if idx == (len(file_data)-1):
            if subplot_num > 0:
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 6)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 5)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 4)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 3)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 2)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 1)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]',fontsize=y_font)
                if subplot_num == 1:
                    ax = fig1.add_subplot(7, 1, 1)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 2:
                    ax = fig1.add_subplot(7, 1, 2)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 3:
                    ax = fig1.add_subplot(7, 1, 3)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 4:
                    ax = fig1.add_subplot(7, 1, 4)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 5:
                    ax = fig1.add_subplot(7, 1, 5)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 6:
                    ax = fig1.add_subplot(7, 1, 6)
                    ax.set_xlabel('Time [hr]')
                elif subplot_num == 7:
                    ax = fig1.add_subplot(7, 1, 7)
                    ax.set_xlabel('Time [hr]')
                if subplot_num <= 6:
                    ax = fig1.add_subplot(7, 1, 7)  # delete plot 7
                    ax.clear()
                if subplot_num <= 5:
                    ax = fig1.add_subplot(7, 1, 6)  # delete plot 6
                    ax.clear()
                if subplot_num <= 4:
                    ax = fig1.add_subplot(7, 1, 5)  # delete plot 5
                    ax.clear()
                if subplot_num <= 3:
                    ax = fig1.add_subplot(7, 1, 4)  # delete plot 4
                    ax.clear()
                if subplot_num <= 2:
                    ax = fig1.add_subplot(7, 1, 3)  # delete plot 3
                    ax.clear()
                if subplot_num <= 1:
                    ax = fig1.add_subplot(7, 1, 2)  # delete plot 2
                    ax.clear()
                plt.tight_layout()
                pdf.savefig(fig1)
    plt.close(fig1)
    pdf.close()


if __name__ == "__main__":

    print("This is a script to analyze the Verisense Raw Data files \n")
    print('ENTER FOLDER LOCATION HERE (use fwd slashs and finish with a fwd slash) \n')
    print('''# example: folder_to_analyze = 'C:/Users/patte/Downloads/CAN001/CAN001/19040201177B/ParsedFiles2/ \n''')
    folder_to_analyze = input("Folder: ")
    warnings.filterwarnings("ignore")

    if folder_to_analyze[-1] != "/":
        #print('Forgot your /, but I added it for you')
        folder_to_analyze = folder_to_analyze + "/"

    # choose accel channel to keep (drop others for speed), and create variables
    acc_channel = 'accZ'  # 'accX' 'accY'
    dir_folder = dir([folder_to_analyze])
    files_list = sorted(os.listdir(folder_to_analyze))
    sorted_list = collections.defaultdict(list)
    duplicate_files = collections.defaultdict(list)
    time_error_files = collections.defaultdict(list)

    file_id = []

    # Attempt to create the output folder if it doesn't exist already
    try:
        if not os.path.exists(folder_to_analyze+"/Verisense_Raw_Acc_QC/"):
            os.makedirs(folder_to_analyze+"/Verisense_Raw_Acc_QC/")
    except OSError:
        print('Error: Creating directory. ' +
              folder_to_analyze+"/Verisense_Raw_Acc_QC/")

    for x in files_list:
        if x[0] == '1' or x[0] == '2':  # check that is starts correctly
            if len(x) > 13:            # check that it has correct naming convenction
                if x[14] == 'A':       # check that file name is correct
                    if x[0:13] not in file_id:  # check that it's not a repeat
                        sorted_list[pd.Timestamp(
                            year=int("20"+x[:2]), month=int(x[2:4]), day=int(x[4:6])).week].append(x)
                        file_id.append(x[0:13])
                    else:
                        duplicate_files[pd.Timestamp(
                            year=int("20"+x[:2]), month=int(x[2:4]), day=int(x[4:6])).week].append(x)
        elif x[0:2] == '70' or x[0:2] == '69':
            time_error_files[pd.Timestamp(
                year=int("20"+x[:2]), month=int(x[2:4]), day=int(x[4:6])).week].append(x)

    # Confirm that we don't have more than 7 graphs per report
    for x in list(sorted_list):
        first = pd.read_csv(folder_to_analyze +
                            sorted_list[x][0], nrows=7, names=('he'))
        first_datetime = datetime(int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(first['h'][3].split(
            "= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]), int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]))
        last_graph = (first_datetime) + timedelta(weeks=1)
        checked = True
        while checked:
            last = pd.read_csv(folder_to_analyze +
                               sorted_list[x][-1], nrows=7, names=('he'))
            last_datetime = datetime(int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]), int(last['h'][4].split(
                "= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]), int(last['h'][4].split("= ", 2)[1].split(' ', 2)[1].split(":", 3)[0]), int(last['h'][4].split("= ", 2)[1].split(' ', 2)[1].split(":", 3)[1]))
            if last_datetime > last_graph:
                # print('true')
                sorted_list[x+1].insert(0, sorted_list[x][-1])
                sorted_list[x].pop(-1)
            else:
                checked = False

    for idx, x in enumerate(sorted_list):
        dfByWeek, dataByWeek, startByWeek, fileByWeek, lenByWeek, deviceName, deviceVersion, firmwareVersion, sample_rate, sensor_range, firstStart = pull_information(
            sorted_list[x])
        plot(fileByWeek, dfByWeek, startByWeek, lenByWeek, dataByWeek, x, deviceName, deviceVersion,
             firmwareVersion, sample_rate, sensor_range, firstStart, duplicate_files[x], time_error_files[x])
