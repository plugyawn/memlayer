| profile | step | k | med loss/loss0 | med corr_norm | bad loss | nonfinite | pos-cos layers | stable layers | median cap multiplier | inner_lr | lr@corr_min | lr@corr_max | lr@median_cap | recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| post-true-k10-lr1e3-alpha0_095056 | 1600 | 10 | 7.789e-01 | 2.842e-02 | 3 | 0 | 11/12 | 9/12 | 3.057e-01 | 1.000e-03 | 3.519e-05 | 3.519e-04 | 3.057e-04 | layer-restrict or gate harder |
| post-true-k10-lr1e4-alpha0_094134 | 1600 | 10 | 9.044e-01 | 4.069e-03 | 0 | 0 | 8/12 | 12/12 | 2.125e+00 | 1.000e-04 | 2.458e-05 | 2.458e-04 | 2.125e-04 | promote active screen |
| post-true-k10-lr2e4-alpha0_094446 | 1600 | 10 | 8.327e-01 | 6.757e-03 | 0 | 0 | 9/12 | 12/12 | 1.262e+00 | 2.000e-04 | 2.960e-05 | 2.960e-04 | 2.524e-04 | promote active screen |
| post-true-k10-lr3e4-alpha0_094751 | 1600 | 10 | 8.297e-01 | 9.128e-03 | 1 | 0 | 9/12 | 11/12 | 9.372e-01 | 3.000e-04 | 3.287e-05 | 3.287e-04 | 2.812e-04 | promote active screen |
| run_kdiag_sequence.nohup | 1600 | 10 | 8.468e-01 | 8.907e-03 | 4 | 0 | 37/48 | 44/48 | 9.577e-01 | nan | nan | nan | nan | layer-restrict or gate harder |
