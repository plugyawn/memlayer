# Optimizer Study Summary

## Paired Validation Deltas

| group | step | active | noop_mean | delta | active_vs_best_noop |
| --- | ---: | ---: | ---: | ---: | ---: |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 0 | 10.8278 | 10.8278 | +0.0000 | +0.0000 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 40 | 5.8661 | 5.8788 | -0.0126 | -0.0063 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 80 | 5.0898 | 5.1166 | -0.0267 | -0.0258 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 120 | 4.3825 | 4.3877 | -0.0052 | -0.0018 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 160 | 4.0497 | 4.0505 | -0.0008 | -0.0004 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | 200 | 3.8840 | 3.8857 | -0.0017 | -0.0014 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 0 | 10.8321 | 10.8321 | +0.0000 | +0.0000 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 40 | 5.8676 | 5.8572 | +0.0104 | +0.0118 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 80 | 5.1044 | 5.1117 | -0.0073 | +0.0060 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 120 | 4.3914 | 4.3905 | +0.0009 | +0.0023 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 160 | 4.0519 | 4.0518 | +0.0001 | +0.0015 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | 200 | 3.8836 | 3.8859 | -0.0023 | -0.0008 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 0 | 10.8271 | 10.8271 | +0.0000 | +0.0000 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 40 | 5.8559 | 5.8674 | -0.0115 | -0.0087 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 80 | 5.0815 | 5.0949 | -0.0134 | +0.0073 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 120 | 4.3943 | 4.3948 | -0.0005 | -0.0001 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 160 | 4.0511 | 4.0509 | +0.0002 | +0.0006 |
| modal_softmuon_sched_all_l01_200_h100_20260531.launch | 200 | 3.8845 | 3.8866 | -0.0021 | -0.0017 |

## Update Perturbations

| group | case | step | surface | layers | blend | delta | cos |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | warmup | 64 | soft_mlp_fc | 0,1 | 1.0000 | 0.2060 | 0.9788 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | paired_active | 50 | soft_mlp_fc | 0,1 | 0.1250 | 0.0229 | 0.9997 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | paired_active | 56 | soft_mlp_fc | 0,1 | 0.5000 | 0.0906 | 0.9959 |
| modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch | paired_active | 64 | soft_mlp_fc | 0,1 | 1.0000 | 0.1842 | 0.9830 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | warmup | 64 | soft_mlp_fc | 0,1 | 1.0000 | 0.2389 | 0.9715 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | warmup | 64 | soft_o | 0,1 | 1.0000 | 0.2894 | 0.9581 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | warmup | 64 | soft_qk | 0,1 | 1.0000 | 0.2398 | 0.9710 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | warmup | 64 | soft_v | 0,1 | 1.0000 | 0.2707 | 0.9633 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 50 | soft_mlp_fc | 0,1 | 0.1250 | 0.0244 | 0.9997 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 50 | soft_o | 0,1 | 0.1250 | 0.0301 | 0.9996 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 50 | soft_qk | 0,1 | 0.1250 | 0.0173 | 0.9999 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 50 | soft_v | 0,1 | 0.1250 | 0.0308 | 0.9995 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 56 | soft_mlp_fc | 0,1 | 0.5000 | 0.0849 | 0.9963 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 56 | soft_o | 0,1 | 0.5000 | 0.1177 | 0.9930 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 56 | soft_qk | 0,1 | 0.5000 | 0.0673 | 0.9977 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 56 | soft_v | 0,1 | 0.5000 | 0.1235 | 0.9923 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 64 | soft_mlp_fc | 0,1 | 1.0000 | 0.1772 | 0.9842 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 64 | soft_o | 0,1 | 1.0000 | 0.2323 | 0.9728 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 64 | soft_qk | 0,1 | 1.0000 | 0.1383 | 0.9904 |
| modal_softmuon_pr291_all_l01_200_h100_20260531.launch | paired_active | 64 | soft_v | 0,1 | 1.0000 | 0.2467 | 0.9695 |
