# Track 3 LocoProp-M 2000 Suffix Decision

Correction note, 2026-06-07:

The original required-line table below was produced from logs that included
prefix validation points, so the target line was anchored at the earliest
parsed control point (`1800`). The suffix analyzer now anchors this check at
`2000` by default. The slope-preservation table remains the relevant read:
existing saved suffix lanes did not preserve the observed `1900->2000` rate.

Control lane: `track3_noloco_ckpt2000_2100_from1800_212259` from `.opencode/current_track3_ledger_20260606_logs/kdepth_461e/suffix_from2000/track3_noloco_ckpt2000_2100_from1800_212259.log`

## Validation Table

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | 3.37337 | 3.37101 | 3.36870 | 3.36658 | 3.36423 | 3.36217 |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | 3.37333 | 3.37098 | 3.36867 | 3.36655 | 3.36420 | nan |
| floor009_to2400_213135 | scheduler | 3.37333 | 3.37099 | 3.36867 | 3.36656 | 3.36420 | 3.36230 |

## Gain Vs Control

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | -0.00004 | -0.00003 | -0.00003 | -0.00003 | -0.00003 | nan |
| floor009_to2400_213135 | scheduler | +0.00000 | -0.00001 | +0.00000 | -0.00001 | +0.00000 | nan |

## Required-Line Check

Target line: from `3.39867 @ 1800` to `3.28000 @ 3000`.

| step | required | control | control - required |
| ---: | ---: | ---: | ---: |
| 2000 | 3.37889 | 3.37333 | -0.00556 |
| 2025 | 3.37642 | 3.37098 | -0.00544 |
| 2050 | 3.37395 | 3.36867 | -0.00528 |
| 2075 | 3.37147 | 3.36655 | -0.00492 |
| 2100 | 3.36900 | 3.36420 | -0.00480 |
| 2125 | 3.36653 | nan | nan |

## Slope Preservation

Reference healthy slope: `0.01140` loss per 100 steps from the observed 1900->2000 window.

| lane | category | window | drop/100 | vs reference | vs required | status |
| --- | --- | --- | ---: | ---: | ---: | --- |
| norm002_locom_to2250_213950 | active_normed | 2000->2100 | 0.00914 | 0.80x | 0.98x | marginal |
| norm002_locom_to2250_213950 | active_normed | 2100->2125 | 0.00824 | 0.72x | 0.88x | cold |
| norm002_locom_to2250_213950 | active_normed | 2000->2125 | 0.00896 | 0.79x | 0.96x | marginal |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | 2000->2100 | 0.00913 | 0.80x | 0.98x | marginal |
| floor009_to2400_213135 | scheduler | 2000->2100 | 0.00913 | 0.80x | 0.98x | marginal |
| floor009_to2400_213135 | scheduler | 2100->2125 | 0.00760 | 0.67x | 0.81x | cold |
| floor009_to2400_213135 | scheduler | 2000->2125 | 0.00882 | 0.77x | 0.95x | marginal |

## Apply-Scale Summary

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | 0.0200 | 0.0200 | 0.0200 | 0.0200 | 0.0200 | 0.0200 |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | nan | nan | nan | nan | nan | nan |
| floor009_to2400_213135 | scheduler | nan | nan | nan | nan | nan | nan |

## Decision

Best active LocoProp gain: -0.00003 at 2075 via `norm002_locom_to2250_213950`.
Best random/orthogonal/parallel gain: nan.
Best scheduler-only gain: +0.00000 at 2000 via `floor009_to2400_213135`.
Best slope preservation: 0.80x on 2000->2100 via `norm002_locom_to2250_213950`.

Read: no lane materially beats control; the 2000 state has likely lost c_fc LocoProp-specific leverage.
Slope read: no lane preserves the 1900->2000 descent rate; this is still a slope-starvation result.
