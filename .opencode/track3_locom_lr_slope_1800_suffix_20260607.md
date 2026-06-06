# Track 3 LocoProp-M LR/Slope Join

## Step Values

| lane | category | step | val_loss | lr_frac |
| --- | --- | ---: | ---: | ---: |
| track3_survival_noloco_from_k5_1800_202043 | control | 1800 | 3.39867 | 0.160000 |
| track3_survival_noloco_from_k5_1800_202043 | control | 1900 | 3.38474 | 0.134444 |
| track3_survival_noloco_from_k5_1800_202043 | control | 2000 | 3.37334 | 0.111111 |
| track3_survival_noloco_from_k5_1800_202043 | control | 2100 | 3.36420 | 0.090000 |
| track3_survival_noloco_from_k5_1800_202043 | control | 2125 | 3.36213 | 0.085069 |
| track3_survival_random_from_k5_1800_194845 | random | 1800 | 3.39870 | 0.160000 |
| track3_survival_random_from_k5_1800_194845 | random | 1900 | 3.38478 | 0.134444 |
| track3_survival_random_from_k5_1800_194845 | random | 2000 | 3.37338 | 0.111111 |
| track3_survival_random_from_k5_1800_194845 | random | 2100 | 3.36424 | 0.090000 |
| track3_survival_random_from_k5_1800_194845 | random | 2125 | 3.36216 | 0.085069 |

## Window Slopes

| lane | category | window | drop | drop/step | rolling target/step | ratio | lr start | lr end | lr drop | status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| track3_survival_noloco_from_k5_1800_202043 | control | 1800->1900 | 0.01393 | 0.0001393 | 0.0000989 | 1.41x | 0.160000 | 0.134444 | 16.0% | healthy |
| track3_survival_noloco_from_k5_1800_202043 | control | 1900->2000 | 0.01140 | 0.0001140 | 0.0000952 | 1.20x | 0.134444 | 0.111111 | 17.4% | healthy |
| track3_survival_noloco_from_k5_1800_202043 | control | 2000->2100 | 0.00914 | 0.0000914 | 0.0000933 | 0.98x | 0.111111 | 0.090000 | 19.0% | marginal |
| track3_survival_noloco_from_k5_1800_202043 | control | 2100->2125 | 0.00207 | 0.0000828 | 0.0000936 | 0.89x | 0.090000 | 0.085069 | 5.5% | cold |
| track3_survival_random_from_k5_1800_194845 | random | 1800->1900 | 0.01392 | 0.0001392 | 0.0000989 | 1.41x | 0.160000 | 0.134444 | 16.0% | healthy |
| track3_survival_random_from_k5_1800_194845 | random | 1900->2000 | 0.01140 | 0.0001140 | 0.0000953 | 1.20x | 0.134444 | 0.111111 | 17.4% | healthy |
| track3_survival_random_from_k5_1800_194845 | random | 2000->2100 | 0.00914 | 0.0000914 | 0.0000934 | 0.98x | 0.111111 | 0.090000 | 19.0% | marginal |
| track3_survival_random_from_k5_1800_194845 | random | 2100->2125 | 0.00208 | 0.0000832 | 0.0000936 | 0.89x | 0.090000 | 0.085069 | 5.5% | cold |

## Read

- `track3_survival_noloco_from_k5_1800_202043`: last healthy `1900->2000`, first cold `2100->2125`.
- `track3_survival_random_from_k5_1800_194845`: last healthy `1900->2000`, first cold `2100->2125`.
