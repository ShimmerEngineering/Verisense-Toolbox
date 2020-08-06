## Verisense Raw Data Visualization Tools

These are python tools for Windows that are run from the command line to create visualizations of raw Verisense sensor data. Simply point the tool to a folder of raw Verisense data and a pdf report will be generated in the same folder with visualizations of the raw data. There are three different .py files that are all called the same way, but produce different reports.

- Verisense_Accel_Report.py
	- One report for all accelerometer data
- Verisense_Accel_Report_Weekly.py
	- A different report for each week of accelerometer data
- Verisense_Gyro_Report_Weekly.py
	- A different report for each week of gyroscope data

The weekly reports are necessary when a large amount of data is being processed to prevent running into memory issues.

### Instructions

- cmd window
- go to folder containing the .py file
- type 'python Verisense_Accel_Report.py' in cmd window to view acceleration data
- if gyroscope data is available, type 'python Verisense_Raw_Gyro_Report_Weekly.py' in cmd window to view gyro data
- then enter path to folder (using either '/' or '\\') in cmd window
- pdf reports(s) will be created in path folder with visualizations


### Dependencies
- python (64-bit)
- following python packages:
	- numpy, pandas, matplotlib, math, datetime and pathlib
  - 'python -m pip install numpy' to install

### Notes
- The tool will take into account different sampling rates
- One of the three acceleration (or gyroscope) channels is plotted in order to reduce processing time

### Example Output
For each week (Mon - Sun) that contains data a separate pdf report is generated. This is what it looks like.
#### Title Page:
![alt text](figs/title_page.jpg)
#### File Information Table:
![alt text](figs/file_info_table.jpg)
#### Raw Data:
![alt text](figs/raw_data.jpg)

### Depreciated Output
This data is no longer being generated in the pdf reports. Code is still available, so they can be turned back on if necessary.
#### Accel Description Table:
![alt text](figs/accel_description_table.jpg)
#### Histogram:
![alt text](figs/histogram.jpg)
