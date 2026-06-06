# Track 3 LocoProp-M Mechanism Report

## Validation And Slope

| log | 1800 | 1900 | 2000 | 2100 | 2125 |
| --- | ---: | ---: | ---: | ---: | ---: |
| noloco_from_k5_1800_202043 | 3.39867 | 3.38474 | 3.37334 | 3.36420 | 3.36213 |
| random_from_k5_1800_194845 | 3.39870 | 3.38478 | 3.37338 | 3.36424 | 3.36216 |
| norm002_locom_to2250_213950 | nan | nan | 3.37337 | 3.36423 | 3.36217 |

| log | window | slope/needed | status |
| --- | --- | ---: | --- |
| noloco_from_k5_1800_202043 | 1800->1900 | 1.41x | healthy |
| noloco_from_k5_1800_202043 | 1900->2000 | 1.20x | healthy |
| noloco_from_k5_1800_202043 | 2000->2100 | 0.98x | marginal |
| noloco_from_k5_1800_202043 | 2100->2125 | 0.89x | cold |
| random_from_k5_1800_194845 | 1800->1900 | 1.41x | healthy |
| random_from_k5_1800_194845 | 1900->2000 | 1.20x | healthy |
| random_from_k5_1800_194845 | 2000->2100 | 0.98x | marginal |
| random_from_k5_1800_194845 | 2100->2125 | 0.89x | cold |
| norm002_locom_to2250_213950 | 2000->2100 | 0.98x | marginal |
| norm002_locom_to2250_213950 | 2100->2125 | 0.88x | cold |

## Local Objective And Direction

| log | step | k | layers | med loss/loss0 | med corr_norm | med cos | good loss | cos>=0 | cos<0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | 2000 | 5 | 12 | 9.119e-01 | 3.672e-03 | 0.006 | 12 | 10 | 2 |
| norm002_locom_to2250_213950 | 2000 | 10 | 12 | 8.609e-01 | 6.382e-03 | 0.006 | 12 | 10 | 2 |
| norm002_locom_to2250_213950 | 2100 | 5 | 12 | 9.201e-01 | 2.873e-03 | 0.009 | 12 | 10 | 2 |
| norm002_locom_to2250_213950 | 2100 | 10 | 12 | 8.721e-01 | 5.198e-03 | 0.009 | 12 | 11 | 1 |
| norm002_locom_to2250_213950 | 2125 | 5 | 12 | 9.158e-01 | 3.216e-03 | 0.004 | 12 | 10 | 2 |
| norm002_locom_to2250_213950 | 2125 | 10 | 12 | 8.588e-01 | 5.766e-03 | 0.004 | 12 | 11 | 1 |

## Applied Correction Scale

| log | step | logged updates | base med | raw frac med | eff frac med | eff frac p90 | scale med |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random_from_k5_1800_194845 | 1800 | 8 | 0.3104 | 4946.8428 | 0.2000 | 0.2001 | 0.000 |
| random_from_k5_1800_194845 | 1900 | 8 | 0.2608 | 5891.1460 | 0.2000 | 0.2000 | 0.000 |
| random_from_k5_1800_194845 | 2000 | 8 | 0.2156 | 7128.2774 | 0.2000 | 0.2001 | 0.000 |
| random_from_k5_1800_194845 | 2100 | 8 | 0.1746 | 8797.2509 | 0.2000 | 0.2001 | 0.000 |
| norm002_locom_to2250_213950 | 2000 | 8 | 0.2155 | 0.0185 | 0.0200 | 0.0200 | 1.087 |
| norm002_locom_to2250_213950 | 2100 | 8 | 0.1746 | 0.0231 | 0.0200 | 0.0200 | 0.867 |
| norm002_locom_to2250_213950 | 2125 | 8 | 0.1650 | 0.0233 | 0.0200 | 0.0200 | 0.861 |

## Mechanism Read

- `noloco_from_k5_1800_202043`: no kdiag rows parsed.
- `random_from_k5_1800_194845`: no kdiag rows parsed.
- `norm002_locom_to2250_213950`: local K10 correction is locally sane at [2000, 2100, 2125]; weak/bad at none.

Synthesis rule: if local loss improves and an applied correction exists but validation slope is still cold, the missing ingredient is not more local iterations. It is trajectory/schedule/state compatibility.
