# Track 3 LocoProp-M Mechanism Report

## Validation And Slope

| log | 1600 | 1700 | 1800 |
| --- | ---: | ---: | ---: |
| k5-lr2e4_192742 | 3.48241 | 3.41883 | 3.39870 |
| k8-lr2e4_190744 | 3.48241 | 3.41884 | 3.39870 |
| k10-lr2e4_184734 | 3.48241 | 3.41884 | 3.39873 |

| log | window | slope/needed | status |
| --- | --- | ---: | --- |
| k5-lr2e4_192742 | 1600->1700 | 4.40x | healthy |
| k5-lr2e4_192742 | 1700->1800 | 1.88x | healthy |
| k8-lr2e4_190744 | 1600->1700 | 4.40x | healthy |
| k8-lr2e4_190744 | 1700->1800 | 1.89x | healthy |
| k10-lr2e4_184734 | 1600->1700 | 4.40x | healthy |
| k10-lr2e4_184734 | 1700->1800 | 1.88x | healthy |

## Local Objective And Direction

| log | step | k | layers | med loss/loss0 | med corr_norm | med cos | good loss | cos>=0 | cos<0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k5-lr2e4_192742 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k5-lr2e4_192742 | 1700 | 5 | 12 | 9.086e-01 | 3.718e-03 | 0.019 | 12 | 10 | 2 |
| k8-lr2e4_190744 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k8-lr2e4_190744 | 1600 | 8 | 12 | 8.589e-01 | 5.750e-03 | 0.005 | 12 | 9 | 3 |
| k8-lr2e4_190744 | 1700 | 5 | 12 | 9.072e-01 | 3.765e-03 | 0.013 | 12 | 12 | 0 |
| k8-lr2e4_190744 | 1700 | 8 | 12 | 8.735e-01 | 5.645e-03 | 0.009 | 11 | 11 | 1 |
| k10-lr2e4_184734 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k10-lr2e4_184734 | 1600 | 8 | 12 | 8.589e-01 | 5.749e-03 | 0.005 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1600 | 10 | 12 | 8.327e-01 | 6.756e-03 | 0.006 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1700 | 5 | 12 | 9.079e-01 | 3.551e-03 | 0.009 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1700 | 8 | 12 | 8.669e-01 | 5.012e-03 | 0.009 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1700 | 10 | 12 | 8.805e-01 | 5.885e-03 | 0.009 | 12 | 11 | 1 |

## Applied Correction Scale

| log | step | logged updates | base med | raw frac med | eff frac med | eff frac p90 | scale med |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k5-lr2e4_192742 | 1600 | 8 | 0.4224 | 0.0104 | 0.0104 | 0.0263 | 1.000 |
| k5-lr2e4_192742 | 1700 | 8 | 0.3643 | 0.0059 | 0.0059 | 0.0153 | 1.000 |
| k8-lr2e4_190744 | 1600 | 8 | 0.4224 | 0.0158 | 0.0158 | 0.0389 | 1.000 |
| k8-lr2e4_190744 | 1700 | 8 | 0.3643 | 0.0097 | 0.0097 | 0.0183 | 1.000 |
| k10-lr2e4_184734 | 1600 | 8 | 0.4224 | 0.0192 | 0.0192 | 0.0465 | 1.000 |
| k10-lr2e4_184734 | 1700 | 8 | 0.3642 | 0.0103 | 0.0103 | 0.0214 | 1.000 |

## Mechanism Read

- `k5-lr2e4_192742`: local K5 correction is locally sane at [1600, 1700]; weak/bad at none.
- `k8-lr2e4_190744`: local K8 correction is locally sane at [1600, 1700]; weak/bad at none.
- `k10-lr2e4_184734`: local K10 correction is locally sane at [1600, 1700]; weak/bad at none.

Synthesis rule: if local loss improves and an applied correction exists but validation slope is still cold, the missing ingredient is not more local iterations. It is trajectory/schedule/state compatibility.
