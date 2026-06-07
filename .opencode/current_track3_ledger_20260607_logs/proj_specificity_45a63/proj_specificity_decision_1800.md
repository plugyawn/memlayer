# Track 3 LocoProp-M Prefix Effect Size

Active: `wr-track3-locom-20260606/.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/extracted/prime_track3_locom_proj_specificity_logs_retry/track3_proj_active_k5_seed3710.log`
Control: `wr-track3-locom-20260606/.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/extracted/prime_track3_locom_proj_specificity_logs_retry/track3_proj_alpha_zero_seed3710.log`
Local-step diagnostic: K=5

## Loss Match

| step | active | alpha_zero | control-active |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48241 | 3.48241 | 0.00000 |
| 1625 | 3.45135 | 3.45137 | 0.00002 |
| 1650 | 3.43561 | 3.43561 | 0.00000 |
| 1675 | 3.42615 | 3.42614 | -0.00001 |
| 1700 | 3.41883 | 3.41882 | -0.00001 |
| 1725 | 3.41288 | 3.41290 | 0.00002 |
| 1750 | 3.40794 | 3.40794 | 0.00000 |
| 1775 | 3.40360 | 3.40361 | 0.00001 |
| 1800 | 3.39870 | 3.39872 | 0.00002 |

Max absolute loss delta on shared screens: `0.00002`
Final control-active delta: `0.00002`

## Gate

Decision step requested: `1800`
Material gain threshold: `0.00100`
Decision delta control-active: `0.00002`
Gate read: `active matches alpha-zero`

## Correction Geometry

| step | median eff_corr/base_step | median cos | median local loss/loss0 | eff*cos |
| ---: | ---: | ---: | ---: | ---: |
| 1600 | 1.943e-02 | 0.0015 | 0.8942 | 2.915e-05 |
| 1625 | 2.803e-02 | 0.0020 | 0.8812 | 5.607e-05 |
| 1650 | 1.755e-02 | -0.0005 | 0.8949 | -8.776e-06 |
| 1675 | 2.555e-02 | 0.0010 | 0.8423 | 2.555e-05 |
| 1700 | 2.798e-02 | 0.0040 | 0.9042 | 1.119e-04 |
| 1725 | 1.813e-02 | 0.0010 | 0.8853 | 1.813e-05 |
| 1750 | 2.326e-02 | 0.0040 | 0.8790 | 9.306e-05 |
| 1775 | 2.735e-02 | 0.0000 | 0.8735 | 0.000e+00 |

## Read

The active and alpha-zero curves are indistinguishable at the logged precision. The applied LocoProp correction did not measurably move validation loss in this prefix.

The `eff*cos` column is the approximate base-descent-aligned component of the applied correction, as a fraction of the Muon step norm. Values near zero mean the correction is mostly sideways relative to the base descent direction.
