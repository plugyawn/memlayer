## Preconditioner
| step | case | name | layers | blend | delta_mean | target_delta_mean | cos_mean | target_cos_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | vsp_metric_skipvr_win48_56 | full_v | 0,1 | 6.2500e-03 | 4.9788e-03 | 0.7966 | 1.0000 | 0.6979 |
| 56 | vsp_metric_skipvr_win48_56 | full_v | 0,1 | 0.0250 | 0.0202 | 0.8075 | 0.9998 | 0.6746 |
| 50 | vsp_metric_skipvr_win48_64 | full_v | 0,1 | 6.2500e-03 | 5.0645e-03 | 0.8103 | 1.0000 | 0.6871 |
| 56 | vsp_metric_skipvr_win48_64 | full_v | 0,1 | 0.0250 | 0.0196 | 0.7858 | 0.9998 | 0.6919 |
| 64 | vsp_metric_skipvr_win48_64 | full_v | 0,1 | 0.0500 | 0.0393 | 0.7867 | 0.9993 | 0.6907 |
## Spectrum
| step | case | name | layer | eig_p50 | eig_p99 | eig_cond | gain_p50 | gain_p99 | gain_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | vsp_metric_skipvr_win48_56 | attn_in | 0 | 0.5190 | 8.9788 | 3.6350e+02 | 1.9267 | 2.8820 | 2.9324 |
| 48 | vsp_metric_skipvr_win48_56 | attn_in | 1 | 0.5096 | 9.6451 | 3.1579e+02 | 1.9623 | 2.9119 | 2.9681 |
| 48 | vsp_metric_skipvr_win48_56 | attn_in | 0 | 0.4663 | 9.7160 | 3.3036e+02 | 2.1444 | 3.1844 | 3.2369 |
| 48 | vsp_metric_skipvr_win48_56 | attn_in | 1 | 0.4775 | 9.9534 | 1.8228e+02 | 2.0942 | 3.1465 | 3.2123 |
| 56 | vsp_metric_skipvr_win48_56 | attn_in | 0 | 0.4435 | 9.9439 | 3.4990e+02 | 2.2545 | 3.3228 | 3.3717 |
| 56 | vsp_metric_skipvr_win48_56 | attn_in | 1 | 0.4598 | 9.6991 | 1.9285e+02 | 2.1746 | 3.2536 | 3.3114 |
| 64 | vsp_metric_skipvr_win48_56 | attn_in | 0 | 0.4259 | 10.0910 | 3.6292e+02 | 2.3481 | 3.4529 | 3.5039 |
| 64 | vsp_metric_skipvr_win48_56 | attn_in | 1 | 0.4463 | 9.5954 | 2.0134e+02 | 2.2406 | 3.3497 | 3.4069 |
| 48 | vsp_metric_skipvr_win48_64 | attn_in | 0 | 0.5189 | 8.8762 | 3.5866e+02 | 1.9272 | 2.8855 | 2.9445 |
| 48 | vsp_metric_skipvr_win48_64 | attn_in | 1 | 0.5096 | 9.3795 | 3.0617e+02 | 1.9622 | 2.9184 | 2.9730 |
| 48 | vsp_metric_skipvr_win48_64 | attn_in | 0 | 0.4654 | 9.9041 | 3.3222e+02 | 2.1486 | 3.1875 | 3.2545 |
| 48 | vsp_metric_skipvr_win48_64 | attn_in | 1 | 0.4758 | 10.3870 | 1.7136e+02 | 2.1018 | 3.1536 | 3.2087 |
| 56 | vsp_metric_skipvr_win48_64 | attn_in | 0 | 0.4433 | 9.9646 | 3.5311e+02 | 2.2558 | 3.3211 | 3.3840 |
| 56 | vsp_metric_skipvr_win48_64 | attn_in | 1 | 0.4588 | 10.1770 | 1.8113e+02 | 2.1794 | 3.2618 | 3.3164 |
| 64 | vsp_metric_skipvr_win48_64 | attn_in | 0 | 0.4248 | 9.8411 | 3.6715e+02 | 2.3542 | 3.4489 | 3.5072 |
| 64 | vsp_metric_skipvr_win48_64 | attn_in | 1 | 0.4459 | 10.0290 | 1.8953e+02 | 2.2429 | 3.3547 | 3.4045 |
## Eigen Energy
| step | case | name | layer | blend | high_low_before | high_low_after | high_low_target | gain_corr_after | gain_corr_target | comm_norm | offdiag_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | vsp_metric_skipvr_win48_56 | full_v | 0 | 6.2500e-03 | 3.3632 | 3.3124 | 0.1517 | -0.8275 | -0.9206 | 0.0179 | 0.7284 |
| 50 | vsp_metric_skipvr_win48_56 | full_v | 1 | 6.2500e-03 | 6.8362 | 6.7080 | 0.1776 | -0.8425 | -0.9482 | 0.0401 | 0.7679 |
| 56 | vsp_metric_skipvr_win48_56 | full_v | 0 | 0.0250 | 5.3546 | 4.9961 | 0.1021 | -0.8136 | -0.9484 | 0.0131 | 0.7180 |
| 56 | vsp_metric_skipvr_win48_56 | full_v | 1 | 0.0250 | 10.1570 | 9.3316 | 0.1373 | -0.8361 | -0.9625 | 0.0321 | 0.7547 |
| 50 | vsp_metric_skipvr_win48_64 | full_v | 0 | 6.2500e-03 | 4.1899 | 4.1231 | 0.1579 | -0.8249 | -0.9241 | 0.0132 | 0.7252 |
| 50 | vsp_metric_skipvr_win48_64 | full_v | 1 | 6.2500e-03 | 7.5565 | 7.4111 | 0.1748 | -0.8347 | -0.9411 | 0.0339 | 0.7735 |
| 56 | vsp_metric_skipvr_win48_64 | full_v | 0 | 0.0250 | 3.1142 | 2.9334 | 0.0944 | -0.8172 | -0.9513 | 0.0111 | 0.6929 |
| 56 | vsp_metric_skipvr_win48_64 | full_v | 1 | 0.0250 | 5.4563 | 5.0754 | 0.1022 | -0.8259 | -0.9581 | 0.0299 | 0.7355 |
| 64 | vsp_metric_skipvr_win48_64 | full_v | 0 | 0.0500 | 2.6445 | 2.3560 | 0.0878 | -0.8197 | -0.9534 | 0.0106 | 0.6695 |
| 64 | vsp_metric_skipvr_win48_64 | full_v | 1 | 0.0500 | 4.7289 | 4.1011 | 0.0917 | -0.8248 | -0.9611 | 0.0281 | 0.7142 |
