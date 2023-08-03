source("verisense_count_steps.R") # update to local path to verisense_count_steps.R file
myfun =  list(FUN=verisense_count_steps,
              parameters= c(3, 5, 15, -0.5, 3, 4, 0.001, 1.2),
              expected_sample_rate= 15,
              expected_unit="g",
              colnames = c("step_count"),
              outputres = 1,
              minlength = 1,
              outputtype="numeric",
              aggfunction = sum,
              timestamp=F,
              reporttype="event")

