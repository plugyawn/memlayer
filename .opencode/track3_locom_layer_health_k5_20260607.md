# Track 3 LocoProp-M Per-Layer Health

Gate approximation: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. The apply logs do not include layer ids, so use this as a layer-health screen, not an exact apply trace.

## k5-lr2e4_192742

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k5-lr2e4_192742.log`
- K: `5`
- selected steps: `1600,1625,1650,1675,1700,1725,1750,1775,1800`

| layer | samples | med loss/loss0 | med gain | med corr_norm | med cos | good loss | accepted | strong | neg cos | unstable | label |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 8 | 9.958e-01 | 4.250e-03 | 7.208e-04 | 0.030 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | accepted-weak |
| 1 | 8 | 9.751e-01 | 2.485e-02 | 1.109e-03 | 0.024 | 1.00 | 0.88 | 0.00 | 0.12 | 0.00 | accepted-weak |
| 2 | 8 | 8.402e-01 | 1.598e-01 | 4.055e-03 | 0.007 | 1.00 | 0.62 | 0.50 | 0.38 | 0.00 | strong |
| 3 | 8 | 9.373e-01 | 6.275e-02 | 2.118e-03 | 0.012 | 1.00 | 0.62 | 0.00 | 0.38 | 0.00 | accepted-weak |
| 4 | 8 | 9.535e-01 | 4.650e-02 | 1.924e-03 | 0.013 | 1.00 | 0.75 | 0.00 | 0.25 | 0.00 | accepted-weak |
| 5 | 8 | 9.461e-01 | 5.395e-02 | 2.260e-03 | 0.013 | 1.00 | 0.88 | 0.00 | 0.12 | 0.00 | accepted-weak |
| 6 | 8 | 9.220e-01 | 7.800e-02 | 3.256e-03 | 0.011 | 1.00 | 0.88 | 0.25 | 0.12 | 0.00 | accepted-weak |
| 7 | 8 | 8.969e-01 | 1.031e-01 | 4.726e-03 | 0.002 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 8 | 8 | 8.747e-01 | 1.253e-01 | 6.016e-03 | 0.004 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 9 | 8 | 8.532e-01 | 1.468e-01 | 8.236e-03 | 0.004 | 1.00 | 0.88 | 0.88 | 0.12 | 0.00 | strong |
| 10 | 8 | 8.366e-01 | 1.634e-01 | 1.098e-02 | 0.009 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | strong |
| 11 | 8 | 8.345e-01 | 1.655e-01 | 1.509e-02 | 0.000 | 1.00 | 0.50 | 0.50 | 0.50 | 0.00 | opposing |

Read:
- strong layers: [2, 7, 8, 9, 10]
- accepted weak/strong layers: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
- risky layers: [11]
- next subset candidate: `WR_LOCOM_LAYER_SET=2,7,8,9,10`

