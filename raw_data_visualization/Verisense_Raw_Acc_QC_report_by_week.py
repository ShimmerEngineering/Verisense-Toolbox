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
                # print(date)
                #print(pd.Timestamp(float(df_head.h[5].split("= ")[1]), unit="ms").month != pd.Timestamp(year=int(date[6:10]),month=int(date[0:2]),day=int(date[3:5]),hour=int(time[0:2]),minute=int(time[3:5]),second=int(time[6:8])).month)
                firstStart = date + " " + time
            time = df_head.h[3][47:55]
            date = df_head.h[3][36:47]

            try:
                startDate = pd.Timestamp(year=int(date[6:10]), month=int(date[3:5]), day=int(
                    date[0:2]), hour=int(time[0:2]), minute=int(time[3:5]), second=int(time[6:8]))
            except ValueError:
                startDate = pd.Timestamp(year=int(date[6:10]), month=int(date[0:2]), day=int(
                    date[3:5]), hour=int(time[0:2]), minute=int(time[3:5]), second=int(time[6:8]))

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


def plot(file_name, df, file_start, file_len_hr, file_data, week, deviceName, deviceVersion, firmwareVersion, sample_rate, sensor_range, firstStart, duplicate_files, time_error_files, hertz):
    if verbose:
        print('Writing the file information, histogram, and Accel description tables', end=' ... ')
   # print('Processing the files \n')
    dict = {'File Name': file_name, 'Start Time': file_start,
            'File Length [hr]': file_len_hr}
    file_info = pd.DataFrame(dict)
    file_info.head()
    df.columns = [acc_channel]

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
        file_path + '/Verisense_Raw_Acc_QC/' + 'raw_acc_' + file_start[0].strftime("%Y%m%d") + "_to_" + file_start[-1].strftime("%Y%m%d") + '.pdf')

    reportDate = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    firstPage = plt.figure(figsize=(12, 12))
    firstPage.clf()
    txt = 'Shimmer Verisense: Raw Acceleration Data Report\n\n Recording Start: ' + firstStart + "\n Report Creation: " + reportDate + '\n [day/month/year] \n\n Recorded by: ' + deviceName + " " + "\n Sensor ID: " + deviceVersion + "\n Firmare Version: " + firmwareVersion + \
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

    if verbose:
        print('Completed.')
        print(' ')

    file_ts = []

    for idx, i_file in enumerate(file_data):
        fs = int(hertz[idx])
        freq = 1000 / fs
        # Faster method of generating time stamps
        file_ts.append(pd.date_range(file_start[idx], freq=str(
            freq)+"ms", periods=len(file_data[idx])))

    import matplotlib.dates as mdates

    fig1 = plt.figure(figsize=(10, 10))
    subplot_num = 0
    curr_day = 0
    y_font = 8  # y-label fontsize
    for idx, i_file in enumerate(file_data):
        if verbose:
            print('Currently drawing ' + file_name[idx], end=' ... ')

        fs = int(hertz[idx])

        samples_per_day = fs*60*60*24

        start_day = file_ts[idx][0].day
        end_day = file_ts[idx][len(file_ts[idx])-1].day
        num_days = end_day - start_day + 1

        # figure out if a new subplot is required: compare start_day to curr_day
        if curr_day == start_day:
            # do not create a new subplot (same day as last one)
            new_day = False
        else:
            new_day = True  # create new subplot

        if num_days > 1:
            start_idx = (file_ts[idx][0].hour * (fs*60*60)) + (file_ts[idx]
                                                               [0].minute * (fs*60)) + (file_ts[idx][0].second * fs)

        if num_days == 1:
            if new_day:
                if subplot_num == 7:
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 6)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 5)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 4)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 3)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 2)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 1)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax.set_xlabel('Time [hr]')
                    plt.tight_layout()
                    pdf.savefig(fig1)
                    subplot_num = 0
                subplot_num += 1

            ax = fig1.add_subplot(7, 1, subplot_num)
            ax.plot(file_ts[idx], i_file, color='red')
            ax.plot(file_ts[idx][0], 0, color='blue',
                    linestyle='None', marker='p', label="Start of file")
            # Remove this blank point if you don't want to have it on the legend
            ax.plot(0, 0, color='black', marker='o',
                    linestyle='None', label='File runs over midnight')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            start_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 0, 0, 0)
            end_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 23, 59, 59) + pd.Timedelta(seconds=1)
            plt.xlim([start_datetime_xlim, end_datetime_xlim])
            plt.ylim([50, -50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()
            curr_day = end_day
            if idx == 0:
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, bbox_to_anchor=(.6,
                                                           1.02, .5, .102), loc=3, ncol=2)

        elif num_days == 2:
            end_idx = samples_per_day - start_idx - 1

            if new_day:
                if subplot_num == 7:
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 6)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 5)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 4)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 3)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 2)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax = fig1.add_subplot(7, 1, 1)
                    ax.grid(True)
                    ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                    ax.set_xlabel('Time [hr]')
                    plt.tight_layout()
                    pdf.savefig(fig1)
                    subplot_num = 0
                subplot_num += 1
            ax = fig1.add_subplot(7, 1, subplot_num)
            ax.plot(file_ts[idx][0:end_idx], i_file[0:end_idx], color='red')
            ax.plot(file_ts[idx][0], 0, color='blue',
                    linestyle='None', marker='p', label="Start of file")
            # Remove this blank point if you don't want to have it on the legend
            ax.plot(0, 0, color='black', marker='o',
                    linestyle='None', label='File runs over midnight')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
            start_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 0, 0, 0)
            end_datetime_xlim = datetime(
                file_ts[idx][0].year, file_ts[idx][0].month, file_ts[idx][0].day, 23, 59, 59) + pd.Timedelta(seconds=1)
            plt.xlim([start_datetime_xlim, end_datetime_xlim])
            plt.ylim([50, -50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()
            if idx == 0:
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, bbox_to_anchor=(.6,
                                                           1.02, .25, .102), loc=3, ncol=2)

            # 2nd plot:
            end_idx += 1
            if subplot_num == 7:
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 6)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 5)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 4)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 3)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 2)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 1)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
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
            plt.ylim([50, -50])
            plt.title(str(start_datetime_xlim.year)+'-' + str(start_datetime_xlim.month) +
                      '-'+str(start_datetime_xlim.day) + ' [y-m-d]')
            plt.tight_layout()
            curr_day = end_day

        # write final block of plots on final element
        if idx == (len(file_data)-1):
            if subplot_num > 0:
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 6)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 5)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 4)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 3)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 2)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
                ax = fig1.add_subplot(7, 1, 1)
                ax.grid(True)
                ax.set_ylabel('AccX [m/s/s]', fontsize=y_font)
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
        print('')

    pdf.savefig(fig1)
    plt.close(fig1)
    pdf.close()


if __name__ == "__main__":

    verbose = True

    if verbose:
        print("This is a script to analyze the Verisense Raw Data files \n")
        print('ENTER FOLDER LOCATION HERE')

    folder_to_analyze = input("Folder: ")

    # folder_to_analyze = 'C:/Users/TRich/Downloads/ParsedRu-20200301T203534Z-001/ParsedRu
    #folder_to_analyze = 'C:/Users/TRich/Documents/ParsedFiles/ParsedFiles3'

    # Ignore warnings, as matplotlib throws a bunch in the middle. Take out for development.
    warnings.filterwarnings("ignore")

    # Verbose logging toggle. Could either ask the user or set it here.

    if verbose:

        print('Checking folder: ' + folder_to_analyze + "\n")

    if ("\\" in folder_to_analyze):
        if verbose:
            print('Replacing your slashes with the correct ones')
        folder_to_analyze = folder_to_analyze.replace("\\", "/")

    if folder_to_analyze[-1] != "/":
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
        if verbose:
            print('Error: Creating directory. ' +
                  folder_to_analyze+"/Verisense_Raw_Acc_QC/")

    if verbose:
        print('\nSorting the files, removing duplicates and time errors.', end=' ... ')

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

    if verbose:
        print('Completed.')
        print('Found ' + str(len(file_id)) + ' unique files to process, ' + str(len(time_error_files)
                                                                                ) + ' time error files, and ' + str(len(duplicate_files)) + ' duplicate files. \n')

    # Check to determine if the function would draw more than 7 graphs, reordering the data until they will only do so.
    if verbose:
        print('Checking to confirm there will only be 7 graphs per page.', end=' ... ')

    for x in list(sorted_list):
        first = pd.read_csv(folder_to_analyze +
                            sorted_list[x][0], nrows=7, names=('he'))
        # Test if there is an issue with the date

    # Use these to test if the format is correct in the dates in the file's headers.
        try:
            first_datetime = datetime(int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(first['h'][3].split(
                "= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]), int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]))
        except ValueError:
            if verbose:
                print('File ' + sorted_list[x][0] +
                      ' has an irregular timestamp ')
            first_datetime = datetime(int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(first['h'][3].split(
                "= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]), int(first['h'][3].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]))

        last_graph = (first_datetime) + timedelta(weeks=1)

        checked = True

        while checked:
            last = pd.read_csv(folder_to_analyze +
                               sorted_list[x][-1], nrows=7, names=('he'))

            try:
                last_datetime = datetime(int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(last['h'][4].split(
                    "= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]), int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]))
            except ValueError:
                if verbose:
                    print('File ' + sorted_list[x][-1] +
                          ' has an irregular timestamp ')
                last_datetime = datetime(int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[2]), int(last['h'][4].split(
                    "= ", 2)[1].split(' ', 2)[0].split('/', 3)[0]), int(last['h'][4].split("= ", 2)[1].split(' ', 2)[0].split('/', 3)[1]))

            if last_datetime > last_graph:
                sorted_list[x+1].insert(0, sorted_list[x][-1])
                sorted_list[x].pop(-1)
            else:
                checked = False
            if sorted_list[x] == []:
                checked = False

    if verbose:
        print('Completed.')

    # Check if there are different hertz in the data, and create a variable to hold it for each file
    if verbose:
        print('\nChecking hertz for each file.', end=' ... ')

    different_hertz = collections.defaultdict(list)
    hertz_list = []

    for x in sorted_list:
        for i in (sorted_list[x]):
            data = pd.read_csv(folder_to_analyze+i, nrows=7, names=('he'))
            hertz = data['h'][6].split("Rate = ", 2)[1].split(".")[0]
            if hertz not in hertz_list:
                hertz_list.append(hertz)
            different_hertz[pd.Timestamp(
                            year=int("20"+i[:2]), month=int(i[2:4]), day=int(i[4:6])).week].append(hertz)

    if verbose:
        print('Completed.')
        print('The different hertz are: ' + str(hertz_list))

    for idx, x in enumerate(sorted_list):
        if verbose:
            print('\nIn week: ' + str(x) + ' which has a total of ' +
                  str(len(sorted_list[x])) + ' files.')
        dfByWeek, dataByWeek, startByWeek, fileByWeek, lenByWeek, deviceName, deviceVersion, firmwareVersion, sample_rate, sensor_range, firstStart = pull_information(
            sorted_list[x])
        plot(fileByWeek, dfByWeek, startByWeek, lenByWeek, dataByWeek, x, deviceName, deviceVersion, firmwareVersion,
             sample_rate, sensor_range, firstStart, duplicate_files[x], time_error_files[x], different_hertz[x])
        if verbose:
            print('Completed week ' + str(x))
    if verbose:
        print('Finished processing.')
