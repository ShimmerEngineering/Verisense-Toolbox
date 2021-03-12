# Verisense Step Count Algorithm for GGIR

The [Verisense](https://verisense.net/) Step Count algorithm is an open source step count algorithm created by [Shimmer Research](http://shimmersensing.com/) to work with the [GGIR R-package](https://cran.r-project.org/web/packages/GGIR/index.html).

The algorithm is based on the [Gu et al, 2017](http://42.121.33.184/upload/resource/paper/sensors-078850306.pdf) method of step detection from tri-axial acceleration data. The algorithm coefficients have been tuned on the [pedometer evaluation dataset](http://cecas.clemson.edu/~ahoover/pedometer/) with an additional pilot dataset to reduce false positives on long term monitoring signals. Details of the validation can be found in the [validation_paper.pdf](validation_paper.pdf) file.

To run the Verisense step count algorithm with GGIR you must:
1. Update the source path to the verisense_count_steps.R function in myscript.R. It should be local on your machine.
2. Source all GGIR functions as normal
3. Source myscript.R
4. Add 'myfun = myfun' as a line to your entry function to GGIR
5. Ensure that do.parallel is set to False in the GGIR entry function
6. Run GGIR and step count per day will be added to part2_daysummary.csv

Further details on using external functions with GGIR can be found [here](https://cran.r-project.org/web/packages/GGIR/vignettes/ExternalFunction.pdf).
