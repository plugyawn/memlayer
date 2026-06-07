# Track 3 LocoProp-M Mechanism Report

## Validation And Slope

| log | 1600 | 1625 | 1700 | 1750 | 1800 | 2000 | 2025 | 2050 | 2125 | 2200 | 2250 | 2500 | 2525 | 2550 | 2575 | 2600 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| active_k5 | 3.48241 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| noloco | 3.48241 | 3.45136 | 3.41884 | 3.40795 | 3.39874 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| prime_track3_2000_suffix_gate_logs/control | nan | nan | nan | nan | nan | 3.37335 | 3.37099 | 3.36867 | 3.36216 | nan | nan | nan | nan | nan | nan | nan |
| floor111_norm002_k5 | nan | nan | nan | nan | nan | 3.37338 | 3.37121 | 3.36932 | 3.36429 | nan | nan | nan | nan | nan | nan | nan |
| natural_k5 | nan | nan | nan | nan | nan | 3.37338 | 3.37102 | 3.36871 | nan | nan | nan | nan | nan | nan | nan | nan |
| tailcopy_43ad37/control | nan | nan | nan | nan | nan | 3.37335 | 3.37099 | 3.36869 | 3.36214 | 3.35627 | 3.35306 | nan | nan | nan | nan | nan |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 3.34115 | 3.34036 | 3.33962 | 3.33891 | 3.33829 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 3.34115 | 3.34037 | 3.33963 | 3.33892 | 3.33830 |

| log | window | slope/needed | status |
| --- | --- | ---: | --- |
| noloco | 1600->1625 | 8.59x | healthy |
| noloco | 1625->1700 | 3.48x | healthy |
| noloco | 1700->1750 | 2.04x | healthy |
| noloco | 1750->1800 | 1.80x | healthy |
| prime_track3_2000_suffix_gate_logs/control | 2000->2025 | 1.01x | healthy |
| prime_track3_2000_suffix_gate_logs/control | 2025->2050 | 0.99x | marginal |
| prime_track3_2000_suffix_gate_logs/control | 2050->2125 | 0.93x | marginal |
| floor111_norm002_k5 | 2000->2025 | 0.93x | marginal |
| floor111_norm002_k5 | 2025->2050 | 0.81x | cold |
| floor111_norm002_k5 | 2050->2125 | 0.71x | cold |
| natural_k5 | 2000->2025 | 1.01x | healthy |
| natural_k5 | 2025->2050 | 0.99x | marginal |
| tailcopy_43ad37/control | 2000->2025 | 1.01x | healthy |
| tailcopy_43ad37/control | 2025->2050 | 0.99x | marginal |
| tailcopy_43ad37/control | 2050->2125 | 0.94x | marginal |
| tailcopy_43ad37/control | 2125->2200 | 0.83x | cold |
| tailcopy_43ad37/control | 2200->2250 | 0.67x | cold |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2500->2525 | 0.26x | cold |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2525->2550 | 0.23x | cold |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2550->2575 | 0.21x | cold |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2575->2600 | 0.18x | cold |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2500->2525 | 0.26x | cold |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2525->2550 | 0.23x | cold |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2550->2575 | 0.21x | cold |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2575->2600 | 0.18x | cold |

## Local Objective And Direction

| log | step | k | layers | med loss/loss0 | med corr_norm | med cos | good loss | cos>=0 | cos<0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| active_k5 | 1600 | 5 | 12 | 9.038e-01 | 4.123e-03 | 0.005 | 12 | 8 | 4 |
| noloco | 1600 | 5 | 12 | 9.038e-01 | 4.124e-03 | 0.005 | 12 | 8 | 4 |
| noloco | 1625 | 5 | 12 | 9.083e-01 | 3.659e-03 | 0.010 | 12 | 9 | 3 |
| noloco | 1700 | 5 | 12 | 9.089e-01 | 3.721e-03 | 0.005 | 12 | 12 | 0 |
| noloco | 1750 | 5 | 12 | 9.142e-01 | 4.001e-03 | 0.016 | 12 | 11 | 1 |
| floor111_norm002_k5 | 2000 | 5 | 12 | 9.127e-01 | 3.661e-03 | 0.010 | 12 | 10 | 2 |
| floor111_norm002_k5 | 2025 | 5 | 12 | 9.178e-01 | 2.842e-03 | 0.009 | 12 | 10 | 2 |
| floor111_norm002_k5 | 2050 | 5 | 12 | 9.202e-01 | 2.906e-03 | 0.006 | 12 | 10 | 2 |
| natural_k5 | 2000 | 5 | 12 | 9.211e-01 | 3.429e-03 | 0.009 | 12 | 10 | 2 |
| natural_k5 | 2025 | 5 | 12 | 9.180e-01 | 2.995e-03 | 0.017 | 12 | 11 | 1 |
| natural_k5 | 2050 | 5 | 12 | 9.216e-01 | 3.024e-03 | 0.007 | 12 | 11 | 1 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2500 | 5 | 12 | 9.142e-01 | 3.533e-03 | 0.009 | 12 | 11 | 1 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2525 | 5 | 12 | 9.242e-01 | 2.588e-03 | 0.009 | 12 | 9 | 3 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2550 | 5 | 12 | 9.187e-01 | 3.528e-03 | 0.008 | 12 | 11 | 1 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2575 | 5 | 12 | 9.202e-01 | 3.132e-03 | 0.007 | 12 | 9 | 3 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2500 | 5 | 12 | 9.142e-01 | 3.783e+01 | 0.009 | 12 | 12 | 0 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2525 | 5 | 12 | 9.186e-01 | 3.745e+01 | 0.007 | 12 | 12 | 0 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2550 | 5 | 12 | 9.110e-01 | 3.754e+01 | 0.008 | 12 | 12 | 0 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2575 | 5 | 12 | 9.150e-01 | 3.767e+01 | 0.009 | 12 | 12 | 0 |

## Applied Correction Scale

| log | step | logged updates | base med | raw frac med | eff frac med | eff frac p90 | scale med |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| active_k5 | 1600 | 8 | 0.4224 | 0.0104 | 0.0104 | 0.0263 | 1.000 |
| noloco | 1600 | 8 | 0.4224 | 0.0104 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1625 | 8 | 0.4075 | 0.0071 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1700 | 8 | 0.3643 | 0.0073 | 0.0000 | 0.0000 | 0.000 |
| noloco | 1750 | 8 | 0.3368 | 0.0065 | 0.0000 | 0.0000 | 0.000 |
| floor111_norm002_k5 | 2000 | 8 | 0.2156 | 0.0111 | 0.0200 | 0.0200 | 1.812 |
| floor111_norm002_k5 | 2025 | 8 | 0.2155 | 0.0092 | 0.0200 | 0.0200 | 2.179 |
| floor111_norm002_k5 | 2050 | 8 | 0.2155 | 0.0123 | 0.0200 | 0.0200 | 1.626 |
| natural_k5 | 2000 | 8 | 0.2156 | 0.0099 | 0.0099 | 0.0272 | 1.000 |
| natural_k5 | 2025 | 8 | 0.2049 | 0.0091 | 0.0091 | 0.0193 | 1.000 |
| natural_k5 | 2050 | 8 | 0.1945 | 0.0106 | 0.0106 | 0.0289 | 1.000 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2500 | 8 | 0.0539 | 0.0445 | 0.0500 | 0.0500 | 1.151 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2525 | 8 | 0.0486 | 0.0422 | 0.0500 | 0.0500 | 1.185 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2550 | 8 | 0.0437 | 0.0447 | 0.0500 | 0.0500 | 1.120 |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2575 | 8 | 0.0389 | 0.0513 | 0.0500 | 0.0500 | 0.976 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2500 | 8 | 0.0539 | 680.5530 | 0.0500 | 0.0500 | 0.000 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2525 | 8 | 0.0486 | 734.7067 | 0.0500 | 0.0500 | 0.000 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2550 | 8 | 0.0436 | 805.0291 | 0.0500 | 0.0500 | 0.000 |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2575 | 8 | 0.0389 | 918.5718 | 0.0500 | 0.0500 | 0.000 |

## Mechanism Read

- `active_k5`: local K5 correction is locally sane at [1600]; weak/bad at none.
- `noloco`: local K5 correction is locally sane at no parsed steps; weak/bad at [1600, 1625, 1700, 1750].
- `prime_track3_2000_suffix_gate_logs/control`: no kdiag rows parsed.
- `floor111_norm002_k5`: local K5 correction is locally sane at [2000, 2025, 2050]; weak/bad at none.
- `natural_k5`: local K5 correction is locally sane at [2000, 2025, 2050]; weak/bad at none.
- `tailcopy_43ad37/control`: no kdiag rows parsed.
- `track3_locom_tail2500_ungated_norm005_seed3710_to2600`: local K5 correction is locally sane at [2500, 2525, 2550, 2575]; weak/bad at none.
- `track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600`: local K5 correction is locally sane at [2500, 2525, 2550, 2575]; weak/bad at none.

Synthesis rule: if local loss improves and an applied correction exists but validation slope is still cold, the missing ingredient is not more local iterations. It is trajectory/schedule/state compatibility.
