## Preconditioner
| step | case | name | layers | blend | delta_mean | target_delta_mean | cos_mean | target_cos_mean | ref_norm_mean | ref_delta_mean | ref_cos_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 64 | lpa_paired_v_mlp_fc_finite_t20_normbase_r02_blend005 | full_mlp_fc_add | 0,1 | 0.0500 | 0.9864 | 19.7280 | 0.9845 | -1.0000 | 1.0000 | 1.2951 | 0.1614 |
| 64 | lpa_paired_v_mlp_fc_finite_t20_normbase_r02_blend005 | full_mlp_fc_add_rawscale | 0,1 | 0.0500 | 0.6527 | 13.0550 | 0.9845 | -0.9946 | 26.1720 | 26.0300 | 0.1614 |
| 64 | lpa_paired_v_mlp_fc_finite_t20_normbase_r02_blend005 | full_v_add | 0,1 | 0.0500 | 0.9483 | 18.9670 | 0.9857 | -0.9999 | 1.0000 | 1.3074 | 0.1453 |
| 64 | lpa_paired_v_mlp_fc_finite_t20_normbase_r02_blend005 | full_v_add_rawscale | 0,1 | 0.0500 | 0.6518 | 13.0360 | 0.9857 | -0.9949 | 7.7677 | 7.6955 | 0.1453 |
| 48 | paired_noop | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9710 |  | 0.9462 |  | 1.0000 | 1.1134 | 0.3800 |
| 48 | paired_noop | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6316 |  | 0.9462 |  | 14.0940 | 13.7470 | 0.3800 |
| 48 | paired_noop | full_v_add | 0,1 | 0.0000e+00 | 0.9391 |  | 0.9774 |  | 1.0000 | 1.2771 | 0.1842 |
| 48 | paired_noop | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6455 |  | 0.9774 |  | 7.8672 | 7.7665 | 0.1842 |
| 50 | paired_noop | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9758 |  | 0.9502 |  | 1.0000 | 1.1414 | 0.3485 |
| 50 | paired_noop | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6336 |  | 0.9502 |  | 16.9820 | 16.6620 | 0.3485 |
| 50 | paired_noop | full_v_add | 0,1 | 0.0000e+00 | 0.9274 |  | 0.9723 |  | 1.0000 | 1.2719 | 0.1910 |
| 50 | paired_noop | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6438 |  | 0.9723 |  | 8.2117 | 8.1189 | 0.1910 |
| 56 | paired_noop | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9816 |  | 0.9375 |  | 1.0000 | 1.1100 | 0.3837 |
| 56 | paired_noop | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6280 |  | 0.9375 |  | 22.6280 | 22.2640 | 0.3837 |
| 56 | paired_noop | full_v_add | 0,1 | 0.0000e+00 | 0.9579 |  | 0.9625 |  | 1.0000 | 1.2787 | 0.1823 |
| 56 | paired_noop | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6407 |  | 0.9625 |  | 13.5130 | 13.3860 | 0.1823 |
| 64 | paired_noop | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9784 |  | 0.9407 |  | 1.0000 | 1.0671 | 0.4305 |
| 64 | paired_noop | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6400 |  | 0.9407 |  | 18.6880 | 18.2820 | 0.4305 |
| 64 | paired_noop | full_v_add | 0,1 | 0.0000e+00 | 0.9498 |  | 0.9708 |  | 1.0000 | 1.2665 | 0.1978 |
| 64 | paired_noop | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6528 |  | 0.9708 |  | 11.7010 | 11.5720 | 0.1978 |
| 50 | paired_active | full_mlp_fc_add | 0,1 | 6.2500e-03 | 0.9758 | 1.5612e+02 | 0.9505 | -1.0000 | 1.0000 | 1.1415 | 0.3484 |
| 50 | paired_active | full_mlp_fc_add_rawscale | 0,1 | 6.2500e-03 | 0.6339 | 1.0143e+02 | 0.9505 | -0.9804 | 16.9130 | 16.5930 | 0.3484 |
| 50 | paired_active | full_v_add | 0,1 | 6.2500e-03 | 0.9307 | 1.4891e+02 | 0.9723 | -0.9996 | 1.0000 | 1.2738 | 0.1886 |
| 50 | paired_active | full_v_add_rawscale | 0,1 | 6.2500e-03 | 0.6439 | 1.0303e+02 | 0.9723 | -0.9901 | 8.4373 | 8.3425 | 0.1886 |
| 56 | paired_active | full_mlp_fc_add | 0,1 | 0.0250 | 0.9823 | 39.2910 | 0.9380 | -1.0000 | 1.0000 | 1.1171 | 0.3759 |
| 56 | paired_active | full_mlp_fc_add_rawscale | 0,1 | 0.0250 | 0.6280 | 25.1210 | 0.9380 | -0.9710 | 23.5090 | 23.1530 | 0.3759 |
| 56 | paired_active | full_v_add | 0,1 | 0.0250 | 0.9568 | 38.2710 | 0.9623 | -0.9998 | 1.0000 | 1.2752 | 0.1868 |
| 56 | paired_active | full_v_add_rawscale | 0,1 | 0.0250 | 0.6407 | 25.6280 | 0.9623 | -0.9841 | 13.4750 | 13.3450 | 0.1868 |
| 64 | paired_active | full_mlp_fc_add | 0,1 | 0.0500 | 0.9796 | 19.5920 | 0.9452 | -1.0000 | 1.0000 | 1.0862 | 0.4100 |
| 64 | paired_active | full_mlp_fc_add_rawscale | 0,1 | 0.0500 | 0.6423 | 12.8460 | 0.9452 | -0.9765 | 19.7030 | 19.3170 | 0.4100 |
| 64 | paired_active | full_v_add | 0,1 | 0.0500 | 0.9558 | 19.1160 | 0.9718 | -0.9998 | 1.0000 | 1.2689 | 0.1947 |
| 64 | paired_active | full_v_add_rawscale | 0,1 | 0.0500 | 0.6530 | 13.0600 | 0.9718 | -0.9890 | 12.7380 | 12.6040 | 0.1947 |
| 48 | paired_noop2 | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9780 |  | 0.9579 |  | 1.0000 | 1.1477 | 0.3413 |
| 48 | paired_noop2 | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6365 |  | 0.9579 |  | 18.0410 | 17.7260 | 0.3413 |
| 48 | paired_noop2 | full_v_add | 0,1 | 0.0000e+00 | 0.9511 |  | 0.9808 |  | 1.0000 | 1.2816 | 0.1787 |
| 48 | paired_noop2 | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6465 |  | 0.9808 |  | 10.1490 | 10.0380 | 0.1787 |
| 50 | paired_noop2 | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9752 |  | 0.9497 |  | 1.0000 | 1.1348 | 0.3560 |
| 50 | paired_noop2 | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6336 |  | 0.9497 |  | 16.5230 | 16.1970 | 0.3560 |
| 50 | paired_noop2 | full_v_add | 0,1 | 0.0000e+00 | 0.9221 |  | 0.9688 |  | 1.0000 | 1.2666 | 0.1976 |
| 50 | paired_noop2 | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6426 |  | 0.9688 |  | 7.4692 | 7.3763 | 0.1976 |
| 56 | paired_noop2 | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9816 |  | 0.9359 |  | 1.0000 | 1.1127 | 0.3808 |
| 56 | paired_noop2 | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6263 |  | 0.9359 |  | 22.8600 | 22.5000 | 0.3808 |
| 56 | paired_noop2 | full_v_add | 0,1 | 0.0000e+00 | 0.9592 |  | 0.9611 |  | 1.0000 | 1.2807 | 0.1797 |
| 56 | paired_noop2 | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6397 |  | 0.9611 |  | 14.2320 | 14.1060 | 0.1797 |
| 64 | paired_noop2 | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9761 |  | 0.9363 |  | 1.0000 | 1.0584 | 0.4398 |
| 64 | paired_noop2 | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6382 |  | 0.9363 |  | 17.1150 | 16.7020 | 0.4398 |
| 64 | paired_noop2 | full_v_add | 0,1 | 0.0000e+00 | 0.9235 |  | 0.9656 |  | 1.0000 | 1.2370 | 0.2344 |
| 64 | paired_noop2 | full_v_add_rawscale | 0,1 | 0.0000e+00 | 0.6513 |  | 0.9656 |  | 8.3588 | 8.2287 | 0.2344 |
| 64 | paired_noop2 | full_mlp_fc_add | 0,1 | 0.0000e+00 | 0.9761 |  | 0.9363 |  | 1.0000 | 1.0584 | 0.4398 |
| 64 | paired_noop2 | full_mlp_fc_add_rawscale | 0,1 | 0.0000e+00 | 0.6382 |  | 0.9363 |  | 17.1150 | 16.7020 | 0.4398 |
| 64 | paired_noop2 | full_v_add | 0,1 | 0.0000e+00 | 0.9235 |  | 0.9656 |  | 1.0000 | 1.2370 | 0.2344 |
