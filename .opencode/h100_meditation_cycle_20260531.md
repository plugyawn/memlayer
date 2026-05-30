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
Data preflight:    CPU-only Modal prepare returned fineweb train shards 1-2 and
                  validation shard, elapsed 0.44s remote
```

Committed during meditation:

```text
9fa7ea4 Add additive component ladder runner
5c85288 Prefer local Modal client for billing check
5577c8f Add paired case summary parser
0c4b06f Add additive correction norm cap
1f6e60a Report early loss in paired summaries
ba5b189 Add preconditioner reference summary parser
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
python3 tools/summarize_precond_refs.py --name full_v_add --name full_v_add_rawscale .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.refs.md
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

Fallback if V component ladder fails:

```text
The paper-focused sidecar recommends switching contract, not continuing V local
correction tuning: run MLP c_fc soft-polar spectral transfer at alpha=0.5,
eps=1e-6, window 48-64, norm-restore on, paired noop/active/noop2. Caveat:
alpha=0.5, eps=6e-5 already lost badly against both noops, so this is a
lower-priority fallback, not a fresh high-confidence path. Rationale: if the V
orthogonal local correction fails, the next distinct mathematical lever is
partial singular-value flattening on the Muon path, not another separate
additive correction. MLP c_fc is the clean 768-dimensional affine surface
already implemented for soft-polar.
```

Fallback command shape:

```bash
NEWTONV_SUITE=softpolar_paired \
NEWTONV_SUITE_LABEL=sp_mlpfc_a05_win48_64 \
SP_STEPS=80 SP_VAL_EVERY=40 \
SP_LAYERS=0-1 SP_WINDOWS=48-64 \
SP_ALPHA=0.5 SP_EPS=1e-6 \
SP_BLEND_MAX=1.0 SP_BLEND_STEPS=16 \
SP_NORM_RESTORE=1 \
SP_PAIRED_CASES=noop,active,noop2 \
SP_LOG_PRECOND=1 SP_LOG_PRECOND_DETAIL=1 \
bash tools/run_newtonv_experiment_suite.sh
```

## Cycle E

```text
GPU block start: 2026-05-31 03:38 IST
GPU block end:   2026-05-31 03:58 IST
Budget:          about 19.6 minutes H100 wall time
App:             ap-wVBWgST7LA4lMC55kwDhqz
Runner:          tools/run_lpa_component_matrix_gate.sh
Next GPU allowed: about 2026-05-31 04:58 IST
```

Artifacts:

```text
.opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_v_components_fixed80_h100_20260531.parsed.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.summary.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.diagnostics.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.refs.md
```

Result:

| component | blend | step 40 delta vs noop mean | step 80 active | noops | step 80 delta vs noop mean | beats both |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| parallel | `0.05` | `+0.0142` | `4.5352` | `4.5336 / 4.5213` | `+0.0077` | no |
| orthogonal | `0.02` | `-0.0394` | `4.5284` | `4.5377 / 4.5272` | `-0.0040` | no |
| orthogonal | `0.05` | `-0.0135` | `4.5258` | `4.5289 / 4.5236` | `-0.0004` | no |

Diagnostic sanity:

```text
parallel full_v_add:
  ref_cos ~= 1.0
  ref_delta ~= 0
  Interpretation: after projection/norm-to-base, this is basically a small
  extra copy of the base NorMuon update. It hurts, so this is not an LR-like win.

orthogonal full_v_add:
  ref_cos ~= 0
  ref_delta ~= sqrt(2)
  Interpretation: the projection test worked and really injected an orthogonal
  base-norm direction scaled by blend.

rawscale orthogonal V:
  ref_norm roughly 8x at step 64 in active cases, with spikes over 20x in noops.
  Natural-magnitude additive needs a true cap if tested.
```

Decision:

```text
Do not promote the V additive finite component form. Orthogonal 0.02 is
suggestive because it beats the mean noop and has a large step-40 signal, but
it does not beat both noops at step 80. Orthogonal 0.05 fades to essentially
parity with the noop mean. Parallel is clearly worse.

This is not a proof that right-preconditioning is useless. It says:
  1. the feature-derived direction is mechanically nontrivial;
  2. pure parallel/LR-like correction is bad;
  3. a small orthogonal component may help briefly;
  4. this finite V additive form is not reliable enough for WR promotion.
```

Meditation targets before another GPU:

```text
1. Decide whether orthogonal 0.02 deserves a replication/finer 0.01/0.02/0.03
   run despite missing the strict beats-both gate.
2. Compare that against switching contracts: true norm-capped natural
   correction, metric-soft V, or MLP c_fc soft-polar with eps=1e-6.
3. Avoid spending the next H100 hour on broad surfaces unless a sidecar can
   explain why this result specifically predicts transfer.
```

## Cycle E Meditation Update

```text
Meditation start: 2026-05-31 03:58 IST
Current check:     2026-05-31 04:10 IST
Next GPU allowed:  about 2026-05-31 04:58 IST
Modal apps:        ap-wVBWgST7LA4lMC55kwDhqz stopped, no active tasks
Repo state:        clean after 8e4d833
```

Read-only sidecar recommendations:

```text
Avicenna:
  Recommendation: run exactly one narrow V orthogonal fine ladder, then kill
  this additive finite V form if it misses.

  Reason: orthogonal:0.02 was not a strict step-80 win because active 4.5284
  missed the best noop 4.5272 by 0.0012. But it beat both noops hard at step
  40 and diagnostics show the injection was mechanically clean: ref_cos ~= 0,
  ref_delta ~= sqrt(2). Parallel 0.05 was bad, so this was not simply an
  LR-like perturbation.

  Proposed run: V only, orthogonal blends 0.01/0.02/0.03, 200 steps.
  Gate: continue only if one case beats both paired noops at step 200 by
  at least 0.003-0.005 and is not only a step-40 blip.

Anscombe:
  Recommendation: switch contracts to true norm-capped natural-magnitude
  additive LPA across v,o,mlp_fc with full component.

  Reason: the orthogonal 0.02 hint is too weak to promote, and forced
  norm-matching may be the wrong intervention. Newton/LocoProp/K-FAC/Shampoo
  all care about curvature-scaled magnitude, while Polar-Muon erases most
  singular-value magnitude. Test a small additive trust-region term capped by
  the Muon update norm instead of renormalizing it to the base update.

  Proposed run: v,o,mlp_fc, component=full, LPA_NORM_TO_BASE=0,
  LPA_NORM_CAP=1, blend=0.05, 80 steps.
  Gate: keep only if one surface beats both paired noops at step 80 and
  improves the noop mean by at least 0.003, without step-40 regression > 0.02
  or step-time overhead > 1%.
```

Decision for next GPU:

```text
Prefer the natural-capped additive surface screen next.

Reason:
  1. The V orthogonal fine ladder is a replication of a near-miss; useful, but
     it mostly asks whether a small no-op-control variance gap flips at 200.
  2. The natural-capped screen asks a distinct mechanistic question: whether
     right-preconditioned magnitude is what gets lost when we force norm-to-base
     or push the metric through Polar/Muon.
  3. It is already implemented, uses fixed paired noops, touches only the
     three most plausible cheap surfaces, and should fit within the next
     one-hour H100 block.
  4. If no surface clears the strict gate, additive LocoProp magnitude in the
     early 48-64 window should be stopped rather than tuned.
```

Prepared command for the 04:58 IST gate:

```bash
NANOGPT_MODAL_GPU='H100!' MODAL_GPU='H100!' MODAL_DETACH=1 \
MODAL_RUN_NAME='lpa-natcap-surface80-20260531' \
MODAL_RUNNER='tools/run_lpa_surface_matrix_gate.sh' \
SCREEN_STEPS=80 SCREEN_VAL_EVERY=40 \
MODAL_EXTRA_ENV_JSON='{"LPA_SUITE_LABEL_PREFIX":"lpa_natcap_surface80_20260531","LPA_SURFACE_MATRIX":"v,o,mlp_fc","LPA_COMPONENT":"full","LPA_NORM_TO_BASE":"0","LPA_NORM_CAP":"1","LPA_STEPS":"80","LPA_VAL_EVERY":"40","LPA_LAYERS":"0-1","LPA_COLLECT_WINDOWS":"0-64","LPA_WINDOWS":"48-64","LPA_REFRESH_INTERVAL":"16","LPA_EMA_BETA":"0.8","LPA_RIDGE_REL":"0.2","LPA_BLEND_MAX":"0.05","LPA_BLEND_STEPS":"16","LPA_FINITE_T":"2.0","LPA_POWER_CLIP":"2.0","LPA_PAIRED_CASES":"noop,active,noop2","LPA_LOG_PRECOND":"1","LPA_LOG_PRECOND_DETAIL":"1"}' \
tools/run_modal_newtonv_raw_gate.sh 2>&1 | tee .opencode/modal_lpa_natcap_surface80_h100_20260531.launch.log
```

Launch guard incident:

```text
At 2026-05-31 04:12 IST a malformed zsh string-comparison guard fell through
early and initialized app ap-KRLqoFpRZZs0WroKYNLsCG. The app was stopped with
`modal app stop -y`, local launcher processes were killed, and `modal app list`
showed the app stopped with 0 tasks. The output only reached image/object
creation logs before the stop; do not count this as a valid H100 experiment.

Fix for the actual gate: do not use zsh `[ ... '<' ... ]`; launch manually or
use a Python wall-clock guard.
```
