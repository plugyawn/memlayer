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

## Cycle D Meditation Update

```text
Meditation start: 2026-05-31 02:38 IST
Current check:     2026-05-31 02:53 IST
Next GPU allowed:  about 2026-05-31 03:38 IST
Modal apps:        all recent apps stopped, no active tasks
Modal billing:     nanogpt-speedrun-newton-muon about $60.01 month-to-date pre-credit
                  exact remaining grant still requires Modal dashboard
```

Committed during meditation:

```text
9fa7ea4 Add additive component ladder runner
5c85288 Prefer local Modal client for billing check
5577c8f Add paired case summary parser
0c4b06f Add additive correction norm cap
```

Sidecar review conclusions:

```text
Both read-only sidecars agreed that the next GPU spend should be the V component
ladder before adding a new rawscale/natural-magnitude correction.

Reason:
  LPA_NORM_TO_BASE=1 projects the right-feature correction, rescales it to the
  base NorMuon update norm, then applies it with additive LR blend. Therefore:
    orthogonal:0.02 = 2% base-norm orthogonal kick
    orthogonal:0.05 = 5% base-norm orthogonal kick
    parallel:0.05 = LR/schedule/control comparator

Rawscale with LPA_NORM_TO_BASE=0 is not a cap unless LPA_NORM_CAP is set.
Existing diagnostics show raw V corrections often around 8-13x the base-update
norm, and MLP/O can be larger. At blend=0.05 that can be a large uncontrolled
perturbation. Commit 0c4b06f added a disabled-by-default cap so the fallback can
use LPA_NORM_TO_BASE=0 plus LPA_NORM_CAP=1 without another implementation cycle.
```

Next H100 ladder:

```bash
NANOGPT_MODAL_GPU='H100!' MODAL_GPU='H100!' MODAL_DETACH=1 \
MODAL_RUN_NAME='lpa-v-components-20260531' \
MODAL_RUNNER='tools/run_lpa_component_matrix_gate.sh' \
SCREEN_STEPS=80 SCREEN_VAL_EVERY=40 \
MODAL_EXTRA_ENV_JSON='{"LPA_COMPONENT_MATRIX":"parallel:0.05,orthogonal:0.02,orthogonal:0.05","LPA_SUITE_LABEL_PREFIX":"lpa_v_components_fixed80_20260531","LPA_SURFACE":"v","LPA_LAYERS":"0-1","LPA_COLLECT_WINDOWS":"0-64","LPA_WINDOWS":"48-64","LPA_REFRESH_INTERVAL":"16","LPA_EMA_BETA":"0.8","LPA_RIDGE_REL":"0.2","LPA_BLEND_STEPS":"16","LPA_FINITE_T":"2.0","LPA_POWER_CLIP":"2.0","LPA_NORM_TO_BASE":"1","LPA_LOG_PRECOND":"1","LPA_LOG_PRECOND_DETAIL":"0"}' \
tools/run_modal_newtonv_raw_gate.sh 2>&1 | tee .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log
```

Post-run parse:

```bash
python3 tools/parse_newtonv_logs.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.parsed.md
python3 tools/summarize_paired_cases.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.summary.md
python3 tools/parse_loco_full_diagnostics.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.diagnostics.md
```

Promotion and falsification:

```text
Promote only if an orthogonal active case beats both noops at step 80 by at
least 0.003-0.005. If orthogonal:0.02 wins and orthogonal:0.05 loses, run
orthogonal 0.01/0.02/0.03 at 200 steps. If parallel wins but orthogonal loses,
treat it as LR/schedule perturbation, not feature-axis alpha. If both
orthogonal cases lose, falsify this additive finite V form for now.

Diagnostic sanity:
  orthogonal full_v_add ref_cos_mean should be near 0
  parallel full_v_add ref_cos_mean should be near +1 or -1
  full_v_add_rawscale should be parsed separately to estimate natural magnitude
```
