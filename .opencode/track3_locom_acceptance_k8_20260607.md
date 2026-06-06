# Track 3 LocoProp-M Accepted-Layer Sequence

Gate reconstruction: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. Apply rows are layerless and logged with cap `8`.

## k8-lr2e4_190744

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k8-lr2e4_190744.log`
- K: `8`
- min_cos: `0.0`

| step | accepted count | accepted layers | logged apply count | count check |
| ---: | ---: | --- | ---: | --- |
| 1600 | 8 | 0,3,4,6,7,8,9,10 | 8 | ok |
| 1625 | 9 | 0,1,3,5,6,7,8,9,11 | 8 | ok capped |
| 1650 | 6 | 0,1,6,7,9,11 | 6 | ok |
| 1675 | 9 | 0,1,2,3,4,5,6,8,10 | 8 | ok capped |
| 1700 | 11 | 0,1,2,3,4,5,6,7,8,9,10 | 8 | ok capped |
| 1725 | 6 | 0,1,3,5,6,8 | 6 | ok |
| 1750 | 10 | 0,1,3,4,5,6,8,9,10,11 | 8 | ok capped |
| 1775 | 12 | 0,1,2,3,4,5,6,7,8,9,10,11 | 8 | ok capped |

Layer acceptance frequency:

| layer | frequency |
| ---: | ---: |
| 0 | 1.00 |
| 1 | 0.88 |
| 2 | 0.38 |
| 3 | 0.88 |
| 4 | 0.62 |
| 5 | 0.75 |
| 6 | 1.00 |
| 7 | 0.62 |
| 8 | 0.88 |
| 9 | 0.75 |
| 10 | 0.62 |
| 11 | 0.50 |

Read:
- most common accepted set: `0,3,4,6,7,8,9,10` (1/8 logged steps)
- count mismatches against apply log: `0`
- gate reconstruction matches the layerless apply-count trace within the logging cap.

