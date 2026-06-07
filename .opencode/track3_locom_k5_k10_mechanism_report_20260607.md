# Track 3 LocoProp-M Mechanism Report

## Validation And Slope

| log | 1600 | 1625 | 1700 | 1750 | 1800 | 2000 | 2050 | 2100 | 2125 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k5-lr2e4_192742 | 3.48241 | 3.45135 | 3.41883 | 3.40793 | 3.39870 | nan | nan | nan | nan |
| k8-lr2e4_190744 | 3.48241 | 3.45135 | 3.41884 | 3.40794 | 3.39870 | nan | nan | nan | nan |
| k10-lr2e4_184734 | 3.48241 | 3.45134 | 3.41884 | 3.40794 | 3.39873 | nan | nan | nan | nan |
| noloco | 3.48241 | 3.45136 | 3.41884 | 3.40795 | 3.39874 | nan | nan | nan | nan |
| norm002_k5 | 3.48241 | 3.45136 | nan | nan | nan | nan | nan | nan | nan |
| control | nan | nan | nan | nan | nan | 3.37335 | 3.36867 | 3.36420 | 3.36216 |
| floor111_norm002_k5 | nan | nan | nan | nan | nan | 3.37338 | 3.36932 | 3.36582 | 3.36429 |
| floor111_norm005_k5 | nan | nan | nan | nan | nan | 3.37338 | 3.36931 | 3.36582 | 3.36430 |
| floor111_random002 | nan | nan | nan | nan | nan | 3.37338 | 3.36931 | 3.36582 | 3.36429 |
| floor111_random005 | nan | nan | nan | nan | nan | 3.37338 | 3.36932 | 3.36581 | 3.36429 |

| log | window | slope/needed | status |
| --- | --- | ---: | --- |
| k5-lr2e4_192742 | 1600->1625 | 8.59x | healthy |
| k5-lr2e4_192742 | 1625->1700 | 3.48x | healthy |
| k5-lr2e4_192742 | 1700->1750 | 2.04x | healthy |
| k5-lr2e4_192742 | 1750->1800 | 1.80x | healthy |
| k8-lr2e4_190744 | 1600->1625 | 8.59x | healthy |
| k8-lr2e4_190744 | 1625->1700 | 3.48x | healthy |
| k8-lr2e4_190744 | 1700->1750 | 2.04x | healthy |
| k8-lr2e4_190744 | 1750->1800 | 1.81x | healthy |
| k10-lr2e4_184734 | 1600->1625 | 8.60x | healthy |
| k10-lr2e4_184734 | 1625->1700 | 3.48x | healthy |
| k10-lr2e4_184734 | 1700->1750 | 2.04x | healthy |
| k10-lr2e4_184734 | 1750->1800 | 1.80x | healthy |
| noloco | 1600->1625 | 8.59x | healthy |
| noloco | 1625->1700 | 3.48x | healthy |
| noloco | 1700->1750 | 2.04x | healthy |
| noloco | 1750->1800 | 1.80x | healthy |
| norm002_k5 | 1600->1625 | 8.59x | healthy |
| control | 2000->2050 | 1.00x | healthy |
| control | 2050->2100 | 0.96x | marginal |
| control | 2100->2125 | 0.87x | cold |
| floor111_norm002_k5 | 2000->2050 | 0.87x | cold |
| floor111_norm002_k5 | 2050->2100 | 0.74x | cold |
| floor111_norm002_k5 | 2100->2125 | 0.64x | cold |
| floor111_norm005_k5 | 2000->2050 | 0.87x | cold |
| floor111_norm005_k5 | 2050->2100 | 0.74x | cold |
| floor111_norm005_k5 | 2100->2125 | 0.64x | cold |
| floor111_random002 | 2000->2050 | 0.87x | cold |
| floor111_random002 | 2050->2100 | 0.74x | cold |
| floor111_random002 | 2100->2125 | 0.64x | cold |
| floor111_random005 | 2000->2050 | 0.87x | cold |
| floor111_random005 | 2050->2100 | 0.75x | cold |
| floor111_random005 | 2100->2125 | 0.64x | cold |

## Local Objective And Direction

| log | step | k | layers | med loss/loss0 | med corr_norm | med cos | good loss | cos>=0 | cos<0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k5-lr2e4_192742 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k5-lr2e4_192742 | 1625 | 5 | 12 | 9.060e-01 | 3.909e-03 | 0.010 | 12 | 11 | 1 |
| k5-lr2e4_192742 | 1700 | 5 | 12 | 9.086e-01 | 3.718e-03 | 0.019 | 12 | 10 | 2 |
| k5-lr2e4_192742 | 1750 | 5 | 12 | 9.116e-01 | 3.775e-03 | 0.014 | 12 | 11 | 1 |
| k8-lr2e4_190744 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k8-lr2e4_190744 | 1600 | 8 | 12 | 8.589e-01 | 5.750e-03 | 0.005 | 12 | 9 | 3 |
| k8-lr2e4_190744 | 1625 | 5 | 12 | 9.045e-01 | 3.914e-03 | 0.007 | 12 | 10 | 2 |
| k8-lr2e4_190744 | 1625 | 8 | 12 | 8.603e-01 | 5.941e-03 | 0.007 | 12 | 10 | 2 |
| k8-lr2e4_190744 | 1700 | 5 | 12 | 9.072e-01 | 3.765e-03 | 0.013 | 12 | 12 | 0 |
| k8-lr2e4_190744 | 1700 | 8 | 12 | 8.735e-01 | 5.645e-03 | 0.009 | 11 | 11 | 1 |
| k8-lr2e4_190744 | 1750 | 5 | 12 | 9.113e-01 | 3.447e-03 | 0.008 | 12 | 11 | 1 |
| k8-lr2e4_190744 | 1750 | 8 | 12 | 8.695e-01 | 5.091e-03 | 0.008 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| k10-lr2e4_184734 | 1600 | 8 | 12 | 8.589e-01 | 5.749e-03 | 0.005 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1600 | 10 | 12 | 8.327e-01 | 6.756e-03 | 0.006 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1625 | 5 | 12 | 9.078e-01 | 3.557e-03 | 0.008 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1625 | 8 | 12 | 8.641e-01 | 5.419e-03 | 0.008 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1625 | 10 | 12 | 8.387e-01 | 6.573e-03 | 0.009 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1700 | 5 | 12 | 9.079e-01 | 3.551e-03 | 0.009 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1700 | 8 | 12 | 8.669e-01 | 5.012e-03 | 0.009 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1700 | 10 | 12 | 8.805e-01 | 5.885e-03 | 0.009 | 12 | 11 | 1 |
| k10-lr2e4_184734 | 1750 | 5 | 12 | 9.150e-01 | 3.327e-03 | 0.006 | 12 | 9 | 3 |
| k10-lr2e4_184734 | 1750 | 8 | 12 | 8.742e-01 | 5.037e-03 | 0.007 | 12 | 10 | 2 |
| k10-lr2e4_184734 | 1750 | 10 | 12 | 8.501e-01 | 6.098e-03 | 0.007 | 12 | 10 | 2 |
| noloco | 1600 | 5 | 12 | 9.038e-01 | 4.124e-03 | 0.005 | 12 | 8 | 4 |
| noloco | 1625 | 5 | 12 | 9.083e-01 | 3.659e-03 | 0.010 | 12 | 9 | 3 |
| noloco | 1700 | 5 | 12 | 9.089e-01 | 3.721e-03 | 0.005 | 12 | 12 | 0 |
| noloco | 1750 | 5 | 12 | 9.142e-01 | 4.001e-03 | 0.016 | 12 | 11 | 1 |
| norm002_k5 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| norm002_k5 | 1625 | 5 | 12 | 9.055e-01 | 3.952e-03 | 0.012 | 12 | 12 | 0 |
| floor111_norm002_k5 | 2000 | 5 | 12 | 9.127e-01 | 3.661e-03 | 0.010 | 12 | 10 | 2 |
| floor111_norm002_k5 | 2050 | 5 | 12 | 9.202e-01 | 2.906e-03 | 0.006 | 12 | 10 | 2 |
| floor111_norm002_k5 | 2100 | 5 | 12 | 9.202e-01 | 2.908e-03 | 0.009 | 12 | 10 | 2 |
| floor111_norm005_k5 | 2000 | 5 | 12 | 9.127e-01 | 3.661e-03 | 0.010 | 12 | 10 | 2 |
| floor111_norm005_k5 | 2050 | 5 | 12 | 9.204e-01 | 3.668e-03 | 0.012 | 12 | 10 | 2 |
| floor111_norm005_k5 | 2100 | 5 | 12 | 9.214e-01 | 3.170e-03 | 0.008 | 12 | 10 | 2 |

## Applied Correction Scale

| log | step | logged updates | base med | raw frac med | eff frac med | eff frac p90 | scale med |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k5-lr2e4_192742 | 1600 | 8 | 0.4224 | 0.0104 | 0.0104 | 0.0263 | 1.000 |
| k5-lr2e4_192742 | 1625 | 8 | 0.4075 | 0.0073 | 0.0073 | 0.0148 | 1.000 |
| k5-lr2e4_192742 | 1700 | 8 | 0.3643 | 0.0059 | 0.0059 | 0.0153 | 1.000 |
| k5-lr2e4_192742 | 1750 | 8 | 0.3368 | 0.0082 | 0.0082 | 0.0183 | 1.000 |
| k8-lr2e4_190744 | 1600 | 8 | 0.4224 | 0.0158 | 0.0158 | 0.0389 | 1.000 |
| k8-lr2e4_190744 | 1625 | 8 | 0.4075 | 0.0115 | 0.0115 | 0.0303 | 1.000 |
| k8-lr2e4_190744 | 1700 | 8 | 0.3643 | 0.0097 | 0.0097 | 0.0183 | 1.000 |
| k8-lr2e4_190744 | 1750 | 8 | 0.3368 | 0.0097 | 0.0097 | 0.0362 | 1.000 |
| k10-lr2e4_184734 | 1600 | 8 | 0.4224 | 0.0192 | 0.0192 | 0.0465 | 1.000 |
| k10-lr2e4_184734 | 1625 | 8 | 0.4075 | 0.0096 | 0.0096 | 0.0361 | 1.000 |
| k10-lr2e4_184734 | 1700 | 8 | 0.3642 | 0.0103 | 0.0103 | 0.0214 | 1.000 |
| k10-lr2e4_184734 | 1750 | 8 | 0.3368 | 0.0120 | 0.0120 | 0.0436 | 1.000 |
| noloco | 1600 | 8 | 0.4224 | 0.0104 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1625 | 8 | 0.4075 | 0.0071 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1700 | 8 | 0.3643 | 0.0073 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1750 | 8 | 0.3368 | 0.0065 | 0.0000 | 0.0000 | 0.000 |
| norm002_k5 | 1600 | 8 | 0.4224 | 0.0104 | 0.0200 | 0.0200 | 1.992 |
| norm002_k5 | 1625 | 8 | 0.4075 | 0.0051 | 0.0200 | 0.0200 | 3.953 |
| floor111_norm002_k5 | 2000 | 8 | 0.2156 | 0.0111 | 0.0200 | 0.0200 | 1.812 |
| floor111_norm002_k5 | 2050 | 8 | 0.2155 | 0.0123 | 0.0200 | 0.0200 | 1.626 |
| floor111_norm002_k5 | 2100 | 8 | 0.2155 | 0.0110 | 0.0200 | 0.0200 | 1.850 |
| floor111_norm005_k5 | 2000 | 8 | 0.2156 | 0.0111 | 0.0500 | 0.0500 | 4.531 |
| floor111_norm005_k5 | 2050 | 8 | 0.2155 | 0.0170 | 0.0500 | 0.0500 | 3.027 |
| floor111_norm005_k5 | 2100 | 8 | 0.2156 | 0.0125 | 0.0500 | 0.0500 | 4.117 |
| floor111_random002 | 2000 | 8 | 0.2156 | 7123.6371 | 0.0200 | 0.0200 | 0.000 |
| floor111_random002 | 2050 | 8 | 0.2155 | 7123.6371 | 0.0200 | 0.0200 | 0.000 |
| floor111_random002 | 2100 | 8 | 0.2155 | 7128.2763 | 0.0200 | 0.0200 | 0.000 |
| floor111_random005 | 2000 | 8 | 0.2156 | 7123.6371 | 0.0500 | 0.0500 | 0.000 |
| floor111_random005 | 2050 | 8 | 0.2155 | 7123.6371 | 0.0500 | 0.0500 | 0.000 |
| floor111_random005 | 2100 | 8 | 0.2156 | 7128.2763 | 0.0500 | 0.0500 | 0.000 |

## Mechanism Read

- `k5-lr2e4_192742`: local K5 correction is locally sane at [1600, 1625, 1700, 1750]; weak/bad at none.
- `k8-lr2e4_190744`: local K8 correction is locally sane at [1600, 1625, 1700, 1750]; weak/bad at none.
- `k10-lr2e4_184734`: local K10 correction is locally sane at [1600, 1625, 1700, 1750]; weak/bad at none.
- `noloco`: local K5 correction is locally sane at no parsed steps; weak/bad at [1600, 1625, 1700, 1750].
- `norm002_k5`: local K5 correction is locally sane at [1600, 1625]; weak/bad at none.
- `control`: no kdiag rows parsed.
- `floor111_norm002_k5`: local K5 correction is locally sane at [2000, 2050, 2100]; weak/bad at none.
- `floor111_norm005_k5`: local K5 correction is locally sane at [2000, 2050, 2100]; weak/bad at none.
- `floor111_random002`: no kdiag rows parsed.
- `floor111_random005`: no kdiag rows parsed.

Synthesis rule: if local loss improves and an applied correction exists but validation slope is still cold, the missing ingredient is not more local iterations. It is trajectory/schedule/state compatibility.

## Conclusion

K-depth is not the missing lever for the current c_fc true-post LocoProp-M
variant. K5, K8, and K10 all improve the local c_fc objective, but the external
validation curve is indistinguishable from the no-correction control through
step 1800.

Correction scale is not the missing lever either. At the step-2000 suffix, the
2% and 5% normalized LocoProp corrections are worse than no-correction by step
2125 and match same-scale random perturbations:

```text
control @2125:        3.36216
norm002_k5 @2125:     3.36429
norm005_k5 @2125:     3.36430
random002 @2125:      3.36429
random005 @2125:      3.36429
```

So the current c_fc additive LocoProp direction is locally sane but externally
inert. More sample tokens, more K, or simple norm scaling should not get more
GPU time. The next useful hypothesis must change the suffix schedule/state, or
change the LocoProp object itself: surface, target, or integration.
