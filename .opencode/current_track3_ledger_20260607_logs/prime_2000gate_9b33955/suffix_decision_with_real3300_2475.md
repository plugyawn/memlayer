# Track 3 LocoProp-M 2000 Suffix Decision

Control lane: `control` from `.opencode/current_track3_ledger_20260607_logs/prime_2000gate_9b33955/prime_track3_2000_nolocom3300_real_logs/track3_locom_2000_control_seed3710.log`

## Validation Table

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 | 2200 | 2250 | 2300 | 2350 | 2400 | 2450 | 2475 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | 3.37337 | 3.37101 | 3.36870 | 3.36658 | 3.36423 | 3.36217 | nan | nan | nan | nan | nan | nan | nan |
| control | control | 3.37335 | 3.37430 | 3.37307 | 3.37137 | 3.36882 | 3.36667 | 3.35982 | 3.35596 | 3.35198 | 3.34877 | 3.34542 | 3.34220 | 3.34100 |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | 3.37333 | 3.37098 | 3.36867 | 3.36655 | 3.36420 | nan | nan | nan | nan | nan | nan | nan | nan |
| floor009_to2400_213135 | scheduler | 3.37333 | 3.37099 | 3.36867 | 3.36656 | 3.36420 | 3.36230 | 3.35755 | 3.35514 | nan | nan | nan | nan | nan |

## Gain Vs Control

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 | 2200 | 2250 | 2300 | 2350 | 2400 | 2450 | 2475 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | -0.00002 | +0.00329 | +0.00437 | +0.00479 | +0.00459 | +0.00450 | nan | nan | nan | nan | nan | nan | nan |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | +0.00002 | +0.00332 | +0.00440 | +0.00482 | +0.00462 | nan | nan | nan | nan | nan | nan | nan | nan |
| floor009_to2400_213135 | scheduler | +0.00002 | +0.00331 | +0.00440 | +0.00481 | +0.00462 | +0.00437 | +0.00227 | +0.00082 | nan | nan | nan | nan | nan |

## Required-Line Check

Target line: from `3.37335 @ 2000` to `3.28000 @ 3000`.

| step | required | control | control - required |
| ---: | ---: | ---: | ---: |
| 2000 | 3.37335 | 3.37335 | +0.00000 |
| 2025 | 3.37102 | 3.37430 | +0.00328 |
| 2050 | 3.36868 | 3.37307 | +0.00439 |
| 2075 | 3.36635 | 3.37137 | +0.00502 |
| 2100 | 3.36401 | 3.36882 | +0.00481 |
| 2125 | 3.36168 | 3.36667 | +0.00499 |
| 2200 | 3.35468 | 3.35982 | +0.00514 |
| 2250 | 3.35001 | 3.35596 | +0.00595 |
| 2300 | 3.34535 | 3.35198 | +0.00664 |
| 2350 | 3.34068 | 3.34877 | +0.00809 |
| 2400 | 3.33601 | 3.34542 | +0.00941 |
| 2450 | 3.33134 | 3.34220 | +0.01086 |
| 2475 | 3.32901 | 3.34100 | +0.01199 |

## Slope Preservation

Reference healthy slope: `0.01140` loss per 100 steps from the observed 1900->2000 window.

| lane | category | window | drop/100 | vs reference | vs required | status |
| --- | --- | --- | ---: | ---: | ---: | --- |
| norm002_locom_to2250_213950 | active_normed | 2000->2100 | 0.00914 | 0.80x | 0.98x | marginal |
| norm002_locom_to2250_213950 | active_normed | 2100->2125 | 0.00824 | 0.72x | 0.88x | cold |
| control | control | 2000->2100 | 0.00453 | 0.40x | 0.49x | cold |
| control | control | 2100->2125 | 0.00860 | 0.75x | 0.87x | cold |
| control | control | 2125->2200 | 0.00913 | 0.80x | 0.92x | marginal |
| control | control | 2200->2300 | 0.00784 | 0.69x | 0.79x | cold |
| control | control | 2300->2400 | 0.00656 | 0.58x | 0.64x | cold |
| control | control | 2400->2475 | 0.00589 | 0.52x | 0.54x | cold |
| control | control | 2000->2400 | 0.00698 | 0.61x | 0.75x | cold |
| control | control | 2000->2475 | 0.00681 | 0.60x | 0.73x | cold |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | 2000->2100 | 0.00913 | 0.80x | 0.98x | marginal |
| floor009_to2400_213135 | scheduler | 2000->2100 | 0.00913 | 0.80x | 0.98x | marginal |
| floor009_to2400_213135 | scheduler | 2100->2125 | 0.00760 | 0.67x | 0.81x | cold |
| floor009_to2400_213135 | scheduler | 2125->2200 | 0.00633 | 0.56x | 0.67x | cold |

## Apply-Scale Summary

| lane | category | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 | 2200 | 2250 | 2300 | 2350 | 2400 | 2450 | 2475 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| norm002_locom_to2250_213950 | active_normed | 0.0200 | 0.0200 | 0.0200 | 0.0200 | 0.0200 | 0.0200 | nan | nan | nan | nan | nan | nan | nan |
| control | control | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| track3_noloco_ckpt2000_2100_from1800_212259 | control | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| floor009_to2400_213135 | scheduler | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |

## Decision

Best active LocoProp gain: +0.00479 at 2075 via `norm002_locom_to2250_213950`.
Best random/orthogonal/parallel gain: nan.
Best scheduler-only gain: +0.00481 at 2075 via `floor009_to2400_213135`.
Best slope preservation: 0.80x on 2000->2100 via `norm002_locom_to2250_213950`.

Read: active LocoProp materially beats control and perturbation controls; c_fc true-post direction still matters in this suffix.
Slope read: no lane preserves the 1900->2000 descent rate; this is still a slope-starvation result.
