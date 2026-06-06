| profile | step | k | med loss/loss0 | med corr_norm | bad loss | nonfinite | pos-cos layers | stable layers | median cap multiplier | inner_lr | lr@corr_min | lr@corr_max | lr@median_cap | recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| post-approx-k10-alpha0 | 1600 | 10 | 3.128e+04 | 1.266e+02 | 8 | 4 | 8/12 | 1/12 | 6.735e-05 | 1.000e-01 | 7.899e-07 | 7.899e-06 | 6.735e-06 | dead: nonfinite correction |
| post-true-k10-alpha0 | 1600 | 10 | 9.890e-01 | 4.685e-04 | 0 | 0 | 8/12 | 12/12 | 1.884e+01 | 1.000e-05 | 2.134e-05 | 2.134e-04 | 1.884e-04 | scale up true local step |
| pre-k10-alpha0 | 1600 | 10 | 6.590e+11 | 3.918e+04 | 11 | 0 | 7/12 | 1/12 | 2.240e-07 | 1.000e-01 | 2.553e-09 | 2.553e-08 | 2.240e-08 | dead: local loss worsens |
