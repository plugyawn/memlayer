# Track 3 LocoProp-M Prefix Effect Size

Active: `/tmp/track3_locom_tick_ladder_20260607/prime_track3_locom_tick_ladder/prefix_specificity/track3_prefix_active_k5_seed3710.log`
Control: `/tmp/track3_locom_tick_ladder_20260607/prime_track3_locom_tick_ladder/prefix_specificity/track3_prefix_noloco_seed3710.log`
Local-step diagnostic: K=5

## Loss Match

| step | active | alpha_zero | control-active |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48242 | 3.48242 | 0.00000 |
| 1625 | 3.45137 | 3.45137 | 0.00000 |
| 1650 | 3.43561 | 3.43563 | 0.00002 |
| 1675 | 3.42615 | 3.42615 | 0.00000 |
| 1700 | 3.41884 | 3.41882 | -0.00002 |
| 1725 | 3.41287 | 3.41288 | 0.00001 |
| 1750 | 3.40794 | 3.40795 | 0.00001 |
| 1775 | 3.40358 | 3.40362 | 0.00004 |
| 1800 | 3.39872 | 3.39873 | 0.00001 |
| 1825 | 3.39517 | 3.39520 | 0.00003 |
| 1850 | 3.39176 | 3.39177 | 0.00001 |
| 1875 | 3.38819 | 3.38821 | 0.00002 |
| 1900 | 3.38478 | 3.38478 | 0.00000 |
| 1925 | 3.38174 | 3.38175 | 0.00001 |
| 1950 | 3.37911 | 3.37912 | 0.00001 |
| 1975 | 3.37607 | 3.37607 | 0.00000 |
| 2000 | 3.37337 | 3.37338 | 0.00001 |

Max absolute loss delta on shared screens: `0.00004`
Final control-active delta: `0.00001`

## Correction Geometry

| step | median eff_corr/base_step | median cos | median local loss/loss0 | eff*cos |
| ---: | ---: | ---: | ---: | ---: |
| 1600 | 7.117e-03 | 0.0040 | 0.9054 | 2.847e-05 |
| 1625 | 5.547e-03 | 0.0095 | 0.9091 | 5.270e-05 |
| 1650 | 6.610e-03 | 0.0140 | 0.9159 | 9.253e-05 |
| 1675 | 5.289e-03 | -0.0020 | 0.9257 | -1.058e-05 |
| 1700 | 6.491e-03 | 0.0130 | 0.9076 | 8.438e-05 |
| 1725 | 1.020e-02 | 0.0045 | 0.9162 | 4.589e-05 |
| 1750 | 8.289e-03 | 0.0150 | 0.9145 | 1.243e-04 |
| 1775 | 6.124e-03 | 0.0065 | 0.9134 | 3.980e-05 |

## Read

The active and alpha-zero curves are indistinguishable at the logged precision. The applied LocoProp correction did not measurably move validation loss in this prefix.

The `eff*cos` column is the approximate base-descent-aligned component of the applied correction, as a fraction of the Muon step norm. Values near zero mean the correction is mostly sideways relative to the base descent direction.
