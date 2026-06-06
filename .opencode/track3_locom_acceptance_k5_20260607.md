# Track 3 LocoProp-M Accepted-Layer Sequence

Gate reconstruction: `accepted ~= loss/loss0 < 1 and cos >= min_cos`. Apply rows are layerless and logged with cap `8`.

## k5-lr2e4_192742

- file: `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/track3_kdepth_k5-lr2e4_192742.log`
- K: `5`
- min_cos: `0.0`

| step | accepted count | accepted layers | logged apply count | count check |
| ---: | ---: | --- | ---: | --- |
| 1600 | 8 | 0,3,4,6,7,8,9,10 | 8 | ok |
| 1625 | 11 | 0,1,2,4,5,6,7,8,9,10,11 | 8 | ok capped |
| 1650 | 8 | 0,1,4,5,6,7,9,10 | 8 | ok |
| 1675 | 7 | 0,1,2,3,5,6,10 | 7 | ok |
| 1700 | 10 | 0,1,2,3,4,5,6,8,9,10 | 8 | ok capped |
| 1725 | 9 | 0,1,4,5,7,8,9,10,11 | 8 | ok capped |
| 1750 | 11 | 0,1,2,3,5,6,7,8,9,10,11 | 8 | ok capped |
| 1775 | 12 | 0,1,2,3,4,5,6,7,8,9,10,11 | 8 | ok capped |

Layer acceptance frequency:

| layer | frequency |
| ---: | ---: |
| 0 | 1.00 |
| 1 | 0.88 |
| 2 | 0.62 |
| 3 | 0.62 |
| 4 | 0.75 |
| 5 | 0.88 |
| 6 | 0.88 |
| 7 | 0.75 |
| 8 | 0.75 |
| 9 | 0.88 |
| 10 | 1.00 |
| 11 | 0.50 |

Read:
- most common accepted set: `0,3,4,6,7,8,9,10` (1/8 logged steps)
- count mismatches against apply log: `0`
- gate reconstruction matches the layerless apply-count trace within the logging cap.

