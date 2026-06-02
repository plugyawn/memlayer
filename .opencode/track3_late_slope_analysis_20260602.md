# Track 3 LocoProp-M Late-Slope Analysis

Date: 2026-06-02

Branch: `codex/wr-fresh-20260526`

Related audit: `.opencode/track3_pr_confirmation_audit_20260602.md`

## Why the 2800 Lead Does Not Land

The best recent seed2900 path had a good state around step `2800`, but the
terminal descent rate was too low.

| run | `@2800` | `@3000` | drop `2800->3000` | per-step drop |
| --- | ---: | ---: | ---: | ---: |
| exact seed2900 replay | `3.30816` | `3.29350` | `0.01466` | `0.0000733` |
| old seed2900 reference | `3.30849` | `3.29374` | `0.01475` | `0.0000737` |
| older seed400 3100 full-LocoProp | `3.31815` | `3.29672` | `0.02143` | `0.0001072` |
| 2400 -> 3000 PR287 cap0.20 suffix | `3.31178` | `3.29683` | `0.01495` | `0.0000748` |

From the exact seed2900 replay state:

| target | required total drop from `3.30816 @2800` | required per-step drop |
| --- | ---: | ---: |
| `3.28 @3000` | `0.02816` | `0.0001408` |
| `3.28 @3030` | `0.02816` | `0.0001224` |
| `3.28 @3100` | `0.02816` | `0.0000939` |

So the exact seed2900 terminal slope is about:

- `52%` of what is needed for `3000`;
- `60%` of what is needed for `3030`;
- `78%` of what is needed for `3100`.

This is why the run looks strong through `2800` and still misses badly.

## What the Suffixes Taught

The suffix tests did not merely fail to help. The cleanest ones directly reduced
terminal slope after their switch point.

| suffix | relevant points | read |
| --- | --- | --- |
| `3030/pr287-tail3125/noloco` | `3.30814 @2800`, `3.30765 @2825`, `3.30602 @2850`, `3.30385 @2875` | worse than exact by `+0.0015` to `+0.0021` after switch |
| `3030/pr287tail3125+loco2800/cap0.20` | `3.30814 @2800`, `3.30775 @2825` | active LocoProp re-on made the next validation worse |
| `3030/pr287-switch/cap0.20` | tracked exact through `2900` | no useful slope change |
| `3030/power0.50/cap0.20` | `3.38188 @2525`, `3.38922 @2550` | too disruptive from checkpoint |

The failure is not a missing late-LocoProp toggle. A simple re-on at `2800`
produced low logged alignment (`cos_desc` around `0.042`, `0.059`, `0.016`,
`-0.013` in the first logged layers) and heavy cap scaling. It then worsened
the validation curve immediately.

## Comparison To Longer Runs

The Prime seed300 long run had a much healthier late slope:

| interval | drop | per-step drop |
| --- | ---: | ---: |
| `2875->3000` | `0.01585` | `0.0001268` |
| `3000->3100` | `0.01268` | `0.0001268` |

That slope is close to what the seed2900 `2800` state would need to hit by
`3030`, but the long-run schedule reaches that regime from a much higher loss.

The target combination is therefore:

```text
keep the seed2900-style mid-run state
retain a Prime/record-style terminal slope
avoid disrupting optimizer state around 2800
```

None of the tested suffixes achieved that combination.

## Launch Gate Going Forward

Do not launch another broad `n=8` wave for the existing primitive unless a new
single-lane test clears one of these gates:

| gate | reason |
| --- | --- |
| `<= 3.302 @2800` | enough state improvement that the current weak slope could maybe still land |
| `<= 3.286 @3000` | close enough that a 3030/3100 finish might be variance-sensitive |
| `<= 3.281 @3030` | direct evidence for the preferred PR window |
| `>= 0.00012` per-step drop from `2800` onward without a worse `2800` state | terminal slope is finally in the right band |

The last gate is the most important. A run that is merely ahead at `1500` or
`2500` is not enough; that pattern has already failed.

## Next Mechanism Class

The next useful experiment should change the terminal optimizer dynamics, not
only the late LocoProp cap or LR horizon. Candidate classes:

1. A current-record substrate plus the same LocoProp-M correction, gated first
   as a single-lane 3000/3030 run.
2. A terminal schedule that preserves high late slope without a discontinuous
   switch at `2800`.
3. A state-decoupled correction that is explicitly disabled if its online
   alignment is weak, rather than relying on the norm cap to rescue direction.

The current exact family should be considered exhausted for PR confirmation.
