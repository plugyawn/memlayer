# Track 3 LocoProp-M Per-Layer Health

Gate approximation: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. The apply logs do not include layer ids, so use this as a layer-health screen, not an exact apply trace.

## k8-lr2e4_190744

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k8-lr2e4_190744.log`
- K: `8`
- selected steps: `1600,1625,1650,1675,1700,1725,1750,1775,1800`

| layer | samples | med loss/loss0 | med gain | med corr_norm | med cos | good loss | accepted | strong | neg cos | unstable | label |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 8 | 9.929e-01 | 7.100e-03 | 1.158e-03 | 0.030 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | accepted-weak |
| 1 | 8 | 9.595e-01 | 4.050e-02 | 1.822e-03 | 0.022 | 1.00 | 0.88 | 0.00 | 0.12 | 0.00 | accepted-weak |
| 2 | 8 | 8.248e-01 | 1.752e-01 | 5.029e-03 | -0.003 | 1.00 | 0.38 | 0.38 | 0.62 | 0.00 | opposing |
| 3 | 8 | 9.405e-01 | 5.955e-02 | 2.521e-03 | 0.016 | 1.00 | 0.88 | 0.25 | 0.12 | 0.00 | accepted-weak |
| 4 | 8 | 9.363e-01 | 6.375e-02 | 2.874e-03 | 0.007 | 1.00 | 0.62 | 0.00 | 0.38 | 0.00 | accepted-weak |
| 5 | 8 | 9.203e-01 | 7.970e-02 | 3.557e-03 | 0.008 | 1.00 | 0.75 | 0.38 | 0.25 | 0.00 | accepted-weak |
| 6 | 8 | 8.860e-01 | 1.140e-01 | 5.087e-03 | 0.013 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | strong |
| 7 | 8 | 8.517e-01 | 1.483e-01 | 7.111e-03 | 0.005 | 1.00 | 0.62 | 0.62 | 0.38 | 0.00 | strong |
| 8 | 8 | 8.202e-01 | 1.798e-01 | 9.036e-03 | 0.007 | 1.00 | 0.88 | 0.88 | 0.12 | 0.00 | strong |
| 9 | 8 | 7.962e-01 | 2.038e-01 | 1.208e-02 | 0.003 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 10 | 8 | 7.768e-01 | 2.232e-01 | 1.592e-02 | 0.006 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 11 | 8 | 7.806e-01 | 2.194e-01 | 2.235e-02 | 0.003 | 0.75 | 0.75 | 0.75 | 0.12 | 0.25 | unstable |

Read:
- strong layers: [6, 7, 8, 9, 10]
- accepted weak/strong layers: [0, 1, 3, 4, 5, 6, 7, 8, 9, 10]
- risky layers: [2, 11]
- next subset candidate: `TRACK3_LOCOM_LAYERS=6,7,8,9,10`

## k10-lr2e4_184734

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k10-lr2e4_184734.log`
- K: `8`
- selected steps: `1600,1625,1650,1675,1700,1725,1750,1775,1800`

| layer | samples | med loss/loss0 | med gain | med corr_norm | med cos | good loss | accepted | strong | neg cos | unstable | label |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 8 | 9.930e-01 | 7.000e-03 | 1.174e-03 | 0.033 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | accepted-weak |
| 1 | 8 | 9.664e-01 | 3.365e-02 | 1.598e-03 | 0.018 | 1.00 | 0.75 | 0.00 | 0.25 | 0.00 | accepted-weak |
| 2 | 8 | 8.302e-01 | 1.698e-01 | 5.161e-03 | 0.006 | 1.00 | 0.50 | 0.50 | 0.50 | 0.00 | opposing |
| 3 | 8 | 9.390e-01 | 6.095e-02 | 2.550e-03 | 0.012 | 1.00 | 0.88 | 0.12 | 0.12 | 0.00 | accepted-weak |
| 4 | 8 | 9.334e-01 | 6.660e-02 | 2.864e-03 | 0.010 | 1.00 | 0.88 | 0.00 | 0.12 | 0.00 | accepted-weak |
| 5 | 8 | 9.218e-01 | 7.820e-02 | 3.453e-03 | 0.008 | 1.00 | 0.88 | 0.12 | 0.12 | 0.00 | accepted-weak |
| 6 | 8 | 8.852e-01 | 1.148e-01 | 4.962e-03 | 0.013 | 1.00 | 1.00 | 1.00 | 0.00 | 0.00 | strong |
| 7 | 8 | 8.520e-01 | 1.480e-01 | 7.107e-03 | 0.011 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 8 | 8 | 8.219e-01 | 1.781e-01 | 8.997e-03 | 0.003 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 9 | 8 | 7.973e-01 | 2.027e-01 | 1.215e-02 | 0.003 | 1.00 | 0.62 | 0.62 | 0.38 | 0.00 | strong |
| 10 | 8 | 7.774e-01 | 2.226e-01 | 1.587e-02 | 0.003 | 1.00 | 0.75 | 0.75 | 0.25 | 0.00 | strong |
| 11 | 8 | 7.774e-01 | 2.226e-01 | 2.155e-02 | 0.001 | 0.88 | 0.50 | 0.50 | 0.38 | 0.12 | strong |

Read:
- strong layers: [6, 7, 8, 9, 10, 11]
- accepted weak/strong layers: [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11]
- risky layers: [2]
- next subset candidate: `TRACK3_LOCOM_LAYERS=6,7,8,9,10,11`

