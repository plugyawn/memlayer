# Track 3 LocoProp-M Accepted-Layer Sequence

Gate reconstruction: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. Apply rows are layerless and logged with cap `8`.

## k10-lr2e4_184734

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k10-lr2e4_184734.log`
- K: `10`
- min_cos: `0.0`

| step | accepted count | accepted layers | logged apply count | count check |
| ---: | ---: | --- | ---: | --- |
| 1600 | 9 | 0,3,4,6,7,8,9,10,11 | 8 | ok capped |
| 1625 | 10 | 0,1,3,4,5,6,7,9,10,11 | 8 | ok capped |
| 1650 | 7 | 0,1,4,5,6,7,11 | 7 | ok |
| 1675 | 7 | 0,2,3,4,5,6,10 | 7 | ok |
| 1700 | 11 | 0,1,2,3,4,5,6,7,8,9,11 | 8 | ok capped |
| 1725 | 10 | 0,1,2,3,4,5,6,7,8,10 | 8 | ok capped |
| 1750 | 10 | 0,1,3,4,5,6,8,9,10,11 | 8 | ok capped |
| 1775 | 11 | 0,1,2,3,4,5,6,7,8,9,10 | 8 | ok capped |

Layer acceptance frequency:

| layer | frequency |
| ---: | ---: |
| 0 | 1.00 |
| 1 | 0.75 |
| 2 | 0.50 |
| 3 | 0.88 |
| 4 | 1.00 |
| 5 | 0.88 |
| 6 | 1.00 |
| 7 | 0.75 |
| 8 | 0.62 |
| 9 | 0.62 |
| 10 | 0.75 |
| 11 | 0.62 |

Read:
- most common accepted set: `0,3,4,6,7,8,9,10,11` (1/8 logged steps)
- count mismatches against apply log: `0`
- gate reconstruction matches the layerless apply-count trace within the logging cap.

