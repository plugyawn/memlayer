# LocoProp-M Mechanism Synthesis, 2026-06-04

## Current read

The strongest evidence for LocoProp-M is still the simple Track 3 prefix family,
not the current-record WR suffix tests.

The useful phase is around `900-1500`: the `cd500` LocoProp family separates
from both the WR-source mean and the older lead seed. The effect is not just a
same-norm random perturbation: the available LocoProp diagnostics show small but
systematic positive directional cosines in the logged shallow `c_fc` layers.

For `c_fc`, the update matrix has about `3072 * 768 = 2.36M` entries. A random
same-shape direction has cosine scale about `1/sqrt(2.36M) ~= 6.5e-4`. A cosine
of `0.03` is therefore roughly `46x` random scale, even though geometrically it
is still nearly orthogonal (`acos(0.03) ~= 88.3 degrees`).

With `norm_cap=0.20`, a `cos=0.03` correction contributes only about
`0.20 * 0.03 = 0.006` of the base step in the base-descent direction. So the
prefix gain is unlikely to be explained by a plain LR-like boost alone. The
working hypothesis is:

```text
LocoProp-M adds a small, statistically nonrandom descent component plus a much
larger feature-conditioned orthogonal component. Random same-norm corrections
match neither the local target residual nor the active feature geometry.
```

## Evidence

From `.opencode/plots/track3_current_comparison_live_20260603_scheduler_refresh7.tsv`:

| run | 1000 | 1250 | 1500 |
| --- | ---: | ---: | ---: |
| WR source n=30 mean | `3.65493` | `3.59611` | `3.53872` |
| lead seed stop@1600 + PR287 | `3.63361` | `3.57134` | `3.51805` |
| cd500 full-LocoProp old-linear seed3704 | `3.60964` | `3.55179` | `3.50016` |
| cd500 LR-comp seed3705 | `3.61013` | `3.55054` | `3.49958` |
| cd500 soft-merge seed3706 | `3.61075` | `3.55302` | `3.50363` |

This makes the mid-run gap roughly:

```text
cd500 family vs WR source mean at 1500: about 0.035-0.039 loss better.
cd500 family vs old lead seed at 1500: about 0.014-0.018 loss better.
```

Available LocoProp diagnostics from `.opencode/current_run_logs/` and
`.opencode/final_stopped_logs_20260603/` in the `875-1500` region show:

```text
875:  l0-l3 cos_desc = 0.027, 0.030, 0.014, 0.083
1000: l0-l3 cos_desc = 0.032, 0.013, 0.033, 0.014
1125: l0-l3 cos_desc = 0.021, 0.012, 0.015, 0.029
1200: l0-l3 cos_desc = 0.050, 0.063, 0.049, 0.011
1250: l0-l3 cos_desc = 0.028, 0.015, 0.005, 0.027
1500: l0-l3 cos_desc = 0.028, 0.011, 0.145, 0.078
```

These are not large as angles, but they are highly nonrandom for a 2.36M-entry
matrix. The logged shallow-layer cosines are also consistently positive in this
window.

The exact-WR-state suffix tests from the saved step-2000 checkpoint did not show
the same behavior:

| suffix from exact WR step 2000 | 2125 result | read |
| --- | ---: | --- |
| no LocoProp control | `3.41121` | control |
| small LR, K10, gated, no normalization | `3.41127` | neutral/slightly worse |
| small LR, K10, no gate, no normalization | `3.41116` | tiny noise-level better |
| norm-to-base cap `0.20`, gated | `3.41234` | worse |
| norm-to-base cap `0.05`, gated | `3.41121` | parity |
| norm-to-base cap `0.10`, `cos>=0.02` | `3.41139` | worse |

So the suffix story is not "LocoProp always helps if scaled correctly." It is
trajectory and phase dependent.

## New control knob

`tools/make_track3_locoprop_m.py` now supports:

```text
TRACK3_LOCOM_CORRECTION_MODE=normal      # default, old behavior
TRACK3_LOCOM_CORRECTION_MODE=orthogonal  # subtract projection onto base descent
TRACK3_LOCOM_CORRECTION_MODE=parallel    # keep only projection onto base descent
```

Diagnostics now log:

```text
raw_cos_desc = cosine before projection filtering
cos_desc     = cosine of the correction actually applied
mode         = correction mode
```

This directly separates the two plausible mechanisms:

```text
parallel succeeds:
    the small positive projection was enough; LocoProp is mostly an LR-like
    aligned correction.

orthogonal succeeds:
    the mostly-orthogonal, feature-conditioned local solve is carrying real
    optimization signal.

normal succeeds but both controls fail:
    the interaction between aligned and orthogonal components matters.
```

## Next no-waste run ladder

Do not spend on suffix screens until the prefix mechanism is answered.

Use the same simple Track 3 prefix setup that produced the `cd500` separation,
then run only to `1500` first:

```text
1. normal LocoProp-M, seed match, to 1500
2. TRACK3_LOCOM_RANDOM_CORRECTION=1, same schedule/cap, to 1500
3. TRACK3_LOCOM_CORRECTION_MODE=orthogonal, same schedule/cap, to 1500
4. TRACK3_LOCOM_CORRECTION_MODE=parallel, same schedule/cap, to 1500
```

Gate:

```text
If orthogonal is within ~0.005 of normal and random is not, preserve LocoProp
as a feature-conditioned orthogonal correction and tune the late schedule.

If only parallel helps, stop treating this as LocoProp geometry; tune it as a
small aligned additive update / LR-shaping effect.

If none reproduce the old `cd500` prefix gap, the old result was schedule or
seed path dependence, not a robust LocoProp mechanism.
```

Only after the `1500` mechanism gate should we run to `3000+`.
