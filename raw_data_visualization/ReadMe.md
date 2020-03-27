## Verisense Raw Data Visualization Tool

This is a python tool for Windows that can be run from the command line to create visualizations in pdf files of a folder of raw Verisense (.csv) recordings. A separate pdf file will be created for each week of raw data. After running the tool, pdf files can be found in the 'Verisense_Raw_Acc_QC' folder inside the folder with the raw data that is being analyzed.

### Instructions

- cmd window
- go to folder containing the .py file
- type 'python Verisense_Raw_Acc_QC_report_by_week.py' in cmd window
- then enter path to folder (using either '/' or '\\') in cmd window
- pdf file(s) will be created in path folder with visualizations


### Dependencies
- python (64-bit)
- following python packages:
	- numpy, pandas, matplotlib and pathlib
  - 'python -m pip install numpy' to install

### Notes
- The tool will take into account different sampling rates
- One of the three acceleration channels is plotted in order to reduce processing time
