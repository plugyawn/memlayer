# Track 3 LocoProp-M Window Health

## Validation Values

| lane | category | 1800 | 1900 | 2000 | 2100 | 2125 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| track3_survival_noloco_from_k5_1800_202043 | control | 3.39867 | 3.38474 | 3.37334 | 3.36420 | 3.36213 |
| track3_survival_random_from_k5_1800_194845 | random | 3.39870 | 3.38478 | 3.37338 | 3.36424 | 3.36216 |

## Required Line

`track3_survival_noloco_from_k5_1800_202043` target line: 3.39867 @ 1800 -> 3.28000 @ 3000

| step | required | actual | actual - required |
| ---: | ---: | ---: | ---: |
| 1800 | 3.39867 | 3.39867 | +0.00000 |
| 1900 | 3.38878 | 3.38474 | -0.00404 |
| 2000 | 3.37889 | 3.37334 | -0.00555 |
| 2100 | 3.36900 | 3.36420 | -0.00480 |
| 2125 | 3.36653 | 3.36213 | -0.00440 |

`track3_survival_random_from_k5_1800_194845` target line: 3.39870 @ 1800 -> 3.28000 @ 3000

| step | required | actual | actual - required |
| ---: | ---: | ---: | ---: |
| 1800 | 3.39870 | 3.39870 | +0.00000 |
| 1900 | 3.38881 | 3.38478 | -0.00403 |
| 2000 | 3.37892 | 3.37338 | -0.00554 |
| 2100 | 3.36902 | 3.36424 | -0.00478 |
| 2125 | 3.36655 | 3.36216 | -0.00439 |

## Window Slopes

| lane | category | window | drop | drop/step | fixed-target ratio | rolling-target ratio | status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| track3_survival_noloco_from_k5_1800_202043 | control | 1800->1900 | 0.01393 | 0.0001393 | 1.41x | 1.41x | healthy |
| track3_survival_noloco_from_k5_1800_202043 | control | 1900->2000 | 0.01140 | 0.0001140 | 1.15x | 1.20x | healthy |
| track3_survival_noloco_from_k5_1800_202043 | control | 2000->2100 | 0.00914 | 0.0000914 | 0.92x | 0.98x | marginal |
| track3_survival_noloco_from_k5_1800_202043 | control | 2100->2125 | 0.00207 | 0.0000828 | 0.84x | 0.89x | cold |
| track3_survival_random_from_k5_1800_194845 | random | 1800->1900 | 0.01392 | 0.0001392 | 1.41x | 1.41x | healthy |
| track3_survival_random_from_k5_1800_194845 | random | 1900->2000 | 0.01140 | 0.0001140 | 1.15x | 1.20x | healthy |
| track3_survival_random_from_k5_1800_194845 | random | 2000->2100 | 0.00914 | 0.0000914 | 0.92x | 0.98x | marginal |
| track3_survival_random_from_k5_1800_194845 | random | 2100->2125 | 0.00208 | 0.0000832 | 0.84x | 0.89x | cold |

## Read

- `track3_survival_noloco_from_k5_1800_202043`: last healthy window `1900->2000`; first cold window `2100->2125`.
- `track3_survival_random_from_k5_1800_194845`: last healthy window `1900->2000`; first cold window `2100->2125`.
