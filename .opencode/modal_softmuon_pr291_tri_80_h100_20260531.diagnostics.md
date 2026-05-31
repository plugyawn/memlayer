## Preconditioner
| step | case | name | layers | blend | delta_mean | target_delta_mean | cos_mean | target_cos_mean | ref_norm_mean | ref_delta_mean | ref_cos_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 64 | mlpfc | soft_mlp_fc | 0,1 | 1.0000 | 0.2296 | 0.2296 | 0.9736 | 0.9736 |  |  |  |
| 50 | mlpfc/paired_active | soft_mlp_fc | 0,1 | 0.1250 | 0.0213 | 0.1706 | 0.9998 | 0.9854 |  |  |  |
| 56 | mlpfc/paired_active | soft_mlp_fc | 0,1 | 0.5000 | 0.1013 | 0.2025 | 0.9948 | 0.9794 |  |  |  |
| 64 | mlpfc/paired_active | soft_mlp_fc | 0,1 | 1.0000 | 0.1482 | 0.1482 | 0.9890 | 0.9890 |  |  |  |
| 64 | all_l01 | soft_mlp_fc | 0,1 | 1.0000 | 0.2253 | 0.2253 | 0.9746 | 0.9746 |  |  |  |
| 64 | all_l01 | soft_o | 0,1 | 1.0000 | 0.2815 | 0.2815 | 0.9604 | 0.9604 |  |  |  |
| 64 | all_l01 | soft_qk | 0,1 | 1.0000 | 0.2294 | 0.2294 | 0.9734 | 0.9734 |  |  |  |
| 64 | all_l01 | soft_v | 0,1 | 1.0000 | 0.2600 | 0.2600 | 0.9662 | 0.9662 |  |  |  |
| 50 | all_l01/paired_active | soft_mlp_fc | 0,1 | 0.1250 | 0.0227 | 0.1815 | 0.9997 | 0.9834 |  |  |  |
| 50 | all_l01/paired_active | soft_o | 0,1 | 0.1250 | 0.0298 | 0.2383 | 0.9996 | 0.9715 |  |  |  |
| 50 | all_l01/paired_active | soft_qk | 0,1 | 0.1250 | 0.0179 | 0.1432 | 0.9998 | 0.9897 |  |  |  |
| 50 | all_l01/paired_active | soft_v | 0,1 | 0.1250 | 0.0303 | 0.2422 | 0.9995 | 0.9706 |  |  |  |
| 56 | all_l01/paired_active | soft_mlp_fc | 0,1 | 0.5000 | 0.1167 | 0.2334 | 0.9932 | 0.9727 |  |  |  |
| 56 | all_l01/paired_active | soft_o | 0,1 | 0.5000 | 0.1233 | 0.2467 | 0.9924 | 0.9695 |  |  |  |
| 56 | all_l01/paired_active | soft_qk | 0,1 | 0.5000 | 0.0877 | 0.1754 | 0.9960 | 0.9839 |  |  |  |
| 56 | all_l01/paired_active | soft_v | 0,1 | 0.5000 | 0.1286 | 0.2572 | 0.9917 | 0.9669 |  |  |  |
| 64 | all_l01/paired_active | soft_mlp_fc | 0,1 | 1.0000 | 0.1740 | 0.1740 | 0.9847 | 0.9847 |  |  |  |
| 64 | all_l01/paired_active | soft_o | 0,1 | 1.0000 | 0.2355 | 0.2355 | 0.9721 | 0.9721 |  |  |  |
| 64 | all_l01/paired_active | soft_qk | 0,1 | 1.0000 | 0.1434 | 0.1434 | 0.9895 | 0.9895 |  |  |  |
| 64 | all_l01/paired_active | soft_v | 0,1 | 1.0000 | 0.2459 | 0.2459 | 0.9698 | 0.9698 |  |  |  |
