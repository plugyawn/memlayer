# Track 3 LocoProp-M Per-Layer Health

Gate approximation: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. The apply logs do not include layer ids, so use this as a layer-health screen, not an exact apply trace.

## k10-lr2e4_184734

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k10-lr2e4_184734.log`
- K: `10`
- selected steps: `1600,1625,1650,1675,1700,1725,1750,1775,1800`

| layer | samples | med loss/loss0 | med gain | med corr_norm | med cos | good loss | accepted | strong | neg cos | unstable | label |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 8 | 9.913e-01 | 8.700e-03 | 1.463e-03 | 0.033 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | accepted-weak |
| 1 | 8 | 9.595e-01 | 4.055e-02 | 1.958e-03 | 0.019 | 1.00 | 0.75 | 0.00 | 0.25 | 0.00 | accepted-weak |
| 2 | 8 | 8.006e-01 | 1.994e-01 | 6.025e-03 | 0.007 | 1.00 | 0.50 | 0.50 | 0.50 | 0.00 | opposing |
| 3 | 8 | 9.300e-01 | 7.000e-02 | 3.012e-03 | 0.013 | 1.00 | 0.88 | 0.25 | 0.12 | 0.00 | accepted-weak |
| 4 | 8 | 9.211e-01 | 7.890e-02 | 3.457e-03 | 0.010 | 1.00 | 1.00 | 0.25 | 0.00 | 0.00 | accepted-weak |
| 5 | 8 | 9.058e-01 | 9.420e-02 | 4.233e-03 | 0.009 | 1.00 | 0.88 | 0.88 | 0.12 | 0.00 | strong |
| 6 | 8 | 8.634e-01 | 1.366e-01 | 6.077e-03 | 0.013 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | strong |
| 7 | 8 | 8.259e-01 | 1.741e-01 | 8.613e-03 | 0.011 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 8 | 8 | 7.912e-01 | 2.088e-01 | 1.083e-02 | 0.003 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 9 | 8 | 7.651e-01 | 2.349e-01 | 1.455e-02 | 0.004 | 1.00 | 0.62 | 0.62 | 0.38 | 0.00 | strong |
| 10 | 8 | 7.434e-01 | 2.566e-01 | 1.886e-02 | 0.004 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 11 | 8 | 7.476e-01 | 2.524e-01 | 2.557e-02 | 0.002 | 0.88 | 0.62 | 0.50 | 0.25 | 0.12 | strong |

Read:
- strong layers: [5, 6, 7, 8, 9, 10, 11]
- accepted weak/strong layers: [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11]
- risky layers: [2]
- next subset candidate: `TRACK3_LOCOM_LAYERS=5,6,7,8,9,10,11`

