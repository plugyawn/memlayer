# H100 / Meditation Cycle Log - 2026-05-31

All times are local IST unless noted.

## Cycle D

```text
GPU block start: 2026-05-31 02:01 IST
GPU block end:   2026-05-31 02:38 IST
Budget:          under the 1 hour H100 allowance
Apps:
  ap-jfbq8qftdizA0vppDREKQS stopped, local-client disconnect during V noop2
  ap-cVsqLgl3enFJjEhP7LtWUw stopped, completed MLP c_fc and O, canceled during QK compile
```

Implementation work:

```text
fc52161 Add paired additive surface screen runner
f4f7791 Prefer local Modal client for GPU runner
87c9be1 Allow detached Modal speedrun screens
```

H100 result files:

```text
.opencode/modal_lpa_surface_matrix_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_surface_rest_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_surface_fixed80_h100_20260531.parsed.md
.opencode/modal_lpa_surface_fixed80_h100_20260531.summary.md
```

Fixed-control additive finite-t surface screen:

| surface | active | noop1 | noop2 | delta vs mean noop | read |
| --- | ---: | ---: | ---: | ---: | --- |
| V | `4.5250` | `4.5250` | incomplete | n/a | no visible active win |
| MLP c_fc | `4.5251` | `4.5235` | `4.5224` | `+0.0022` | worse |
| O headwise | `4.5239` | `4.5189` | `4.5209` | `+0.0040` | worse |
| QK | incomplete | incomplete | incomplete | n/a | canceled during compile |

Conclusion:

```text
The state-decoupled additive LocoProp-style correction is not currently a hit
under fixed paired controls. The earlier positive additive results were likely
from the broken runtime-noop path or control spread, not stable optimizer alpha.

The additive diagnostics need careful interpretation. The `target_cos` field is
not meaningful for additive corrections because the logger assumes an in-place
blended preconditioner, while additive uses `blend` later as a separate LR
scale. The meaningful field is `ref_cos`, which measures the local correction
against the base NorMuon update:

  V:      ref_cos around 0.15-0.20
  MLP fc: ref_cos around 0.16-0.39
  O:      ref_cos around 0.15-0.30

So the local correction is not sign-flipped. It is weakly positive-aligned with
the base update, and the raw unnormalized correction often has a much larger
norm than the base update. The current "add normalized GC-filtered correction on
top of NorMuon" interpretation is therefore suspect because it may mostly be a
small extra partially aligned step, not because it points exactly backward.

The right-feature axis is still theoretically real, but the usable form is not:
  1. hard Muon-path insertion gets washed/confounded,
  2. post-varred/full-metric insertion faded,
  3. additive finite correction fights the base update,
  4. soft/metric-soft V did not beat paired noops.
```

Next meditation targets:

```text
1. Explain why right-preconditioned raw gradients are only weakly aligned with
   the NorMuon base update after cautious/variance-reduced polar.
2. Test whether additive correction needs projection control: parallel-only,
   orthogonal-only, or norm cap below 5%.
3. Verify the sign convention with a tiny deterministic local tensor test, but
   do not treat `target_cos` as evidence for a sign bug in additive mode.
4. Avoid further H100 screens until we resolve this directionality issue from
   diagnostics or a tiny deterministic local tensor test.
```
