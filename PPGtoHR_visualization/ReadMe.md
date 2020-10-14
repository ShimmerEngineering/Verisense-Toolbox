# PPG Visualization Tools

There are two scripts available in this repo for analyzing Verisense PPG to HR data:
1. Visualize Raw and Processed Results
    - Raw_and_Processed_PPG_viz.py  
2. Visualize Processed Results
    - Processed_PPG_viz.py

## How to Run: Raw_and_Processed_PPG_viz.py
- go to command window
- go to folder containing the Raw_and_Processed_PPG_viz.py script
- in command window type 'python Raw_and_Processed_PPG_viz.py'
- enter the file path (using forward slashes) to the raw data (ParsedFiles)
- script will create a pdf in the data folder with graphs
  - Raw PPG plotted with HR values from the algorithm
  - HR coverage in % reported on graph
  - Mean HR [bpm] reported on graph as well
- 4 graphs per page
- script will also create a csv file in the raw data folder with performance metrics on each snippet (HR coverage and mean-HR)


## How to Run: Processed_PPG_viz.py
- go to command window
- go to folder containing the Processed_PPG_viz.py script
- in command window type 'python Processed_PPG_viz.py'
- enter the file path (using forward slashes) to the processed data (PPGtoHR)
- decide if you want to see HR (0) or IBI (0)
- script will create a pdf in the data folder with graphs
  - 16 graphs per page showing either HR or IBI in each snippet
- script will also create a csv in the data folder with performance metrics on each snippet



## Requirements
- Windows 10
- 64-bit Python 3.8 (at time of writing 14th Oct 2020, the Panda package does not support Python 3.9)
- Install the following packages:
  - pandas
  - numpy
  - matplotlib
  - DateTime
