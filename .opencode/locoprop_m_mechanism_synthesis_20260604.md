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
TRACK3_LOCOM_CORRECTION_MODE=normal                # default, old behavior
TRACK3_LOCOM_CORRECTION_MODE=orthogonal            # subtract projection onto base descent
TRACK3_LOCOM_CORRECTION_MODE=parallel              # keep only projection onto base descent
TRACK3_LOCOM_CORRECTION_MODE=polar                 # Muon/NS polarize LocoProp correction
TRACK3_LOCOM_CORRECTION_MODE=softpolar             # PR291-style soft polarize correction
TRACK3_LOCOM_CORRECTION_MODE=orthogonal_polar      # lateral part, then hard polar
TRACK3_LOCOM_CORRECTION_MODE=orthogonal_softpolar  # lateral part, then soft polar
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

polar/softpolar succeeds:
    LocoProp's matrix subspace is useful, but its local-solve spectrum is out
    of scale for the global optimizer.
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
5. TRACK3_LOCOM_CORRECTION_MODE=softpolar, same schedule/cap, to 1500
6. TRACK3_LOCOM_CORRECTION_MODE=orthogonal_softpolar, same schedule/cap, to 1500
```

Gate:

```text
If orthogonal is within ~0.005 of normal and random is not, preserve LocoProp
as a feature-conditioned orthogonal correction and tune the late schedule.

If only parallel helps, stop treating this as LocoProp geometry; tune it as a
small aligned additive update / LR-shaping effect.

If softpolar beats normal, keep the LocoProp direction but stop trusting the raw
local-solve singular values. Hard `polar` is a sharper science control, but
`softpolar` should be the first WR-facing polar variant.

If none reproduce the old `cd500` prefix gap, the old result was schedule or
seed path dependence, not a robust LocoProp mechanism.
```

Only after the `1500` mechanism gate should we run to `3000+`.

## 2026-06-04 Prime H100 mode checks

Provider/runtime:

```text
Prime Datacrunch H100 SXM5, seed offset 3704
source: records/track_3_optimization/train_gpt_simple.py
horizon: 3000-step LR schedule
LocoProp-M: K=4, sample_tokens=2048, inner_lr=0.1, prox=0.1, norm_cap=0.20
aux_capture=1, aux_seqs=16, batched_prep=1
```

Pulled logs:

```text
.opencode/prime_track3_locom_modes_20260604/
```

Results:

| mode | screen | val | note |
| --- | ---: | ---: | --- |
| `softpolar` | 125 | 4.64606 | worse than useful same-horizon band |
| `softpolar` | 250 | 4.11736 | stopped early; post-softpolar cosines were near zero or negative |
| `orthogonal` | 125 | 4.63267 | better than softpolar, but not a proof point |
| `orthogonal` | 250 | 4.11543 | diagnostic only; 250 is too early for the 3000-horizon question |
| `orthogonal` | 375 | 3.93006 | tracks weak same-horizon behavior |
| `orthogonal` | 450 | 3.86217 | no breakout |
| `orthogonal` | 500 | 3.82706 | worse than the useful same-horizon references |
| `normal` | 125 | 4.64466 | same setup control; also weak |
| `normal` | 250 | 4.11248 | slightly ahead of projection modes, but not a meaningful later-screen proof |
| `normal` | 375 | 3.93091 | weak same-horizon behavior |
| `normal` | 475 | 3.84222 | no strong prefix reproduction |
| `normal` | 500 | 3.82583 | only `0.00123` better than orthogonal, still weak |

Mechanism read:

```text
normal being weak says: this exact 3000-horizon Prime setup did not reproduce
the old strong 500-step LocoProp prefix.
softpolar failing says: do not just polar/soft-polar the LocoProp direction.
orthogonal matching normal says: the old gain was not just same-size lateral
motion, and today's weak behavior is not fixed by removing the parallel part.
```

The working hypothesis is now narrower:

```text
The useful LocoProp-M prefix, when it appears, likely depends more on the
LR/state phase than on a universally helpful correction transform. The coupled
parallel + orthogonal structure of the raw local correction may still matter,
but this screen says projection/polar controls are not the immediate fix.
```

The orthogonal diagnostics also show why a simple cosine story is incomplete.
At step 250 one layer had `raw_cos_desc=0.763` but an enormous local correction
norm, and projection forced the applied cosine to zero. This creates a capped
lateral displacement but discards the aligned component that may be part of the
real correction.

## Corrected decision gates

Step `250` is not a decision reference for the current hypothesis. It is only a
smoke screen for broken code, catastrophic schedule mismatch, or obvious local
solve harm. The LocoProp-M question is phase dependent, so ranking variants at
`250` answers the wrong problem.

Use these gates instead:

| gate | purpose |
| ---: | --- |
| `900-1250` | first meaningful prefix separation on 3000-ish schedules |
| `1500-1600` | whether the LocoProp prefix state is actually better before handoff |
| `2000-2200` | whether the optimizer handoff preserves slope instead of flattening |
| `2400-2500` | whether the WR-style late optimizer is catching up or being stifled |
| `2800-3000` | terminal slope; this decides whether the run can actually land below `3000` |

The earlier `softpolar` / `orthogonal` Prime checks are therefore only path
checks. They say the projection/polar variants did not obviously rescue the
mechanism, but they do not settle whether LocoProp-M helps in the actual
`900+` schedule phase.

## Next conservative probe

The best remaining low-spend experiment is not another correction-mode screen.
It is an optimizer-state handoff probe:

```text
model state:
  LocoProp-improved simple Track 3 prefix checkpoint at step 1600

optimizer state:
  current-record WR source checkpoint at the matching step

variant:
  load Adam state only, do not hard-load Muon/SOAP optimizer2 state
```

This sits between the two failures already observed:

```text
cold WR suffix:
  may lose mature late optimizer geometry

hard mature WR optimizer splice:
  immediate model-state advantage, then flattening from nonportable optimizer state
```

The exact run should use:

```bash
RUN_LABEL=wr_resume_locom1600_adamonly_seed3710
WR_RESUME_MODEL_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
WR_RESUME_OPTIMIZER_CHECKPOINT=/root/.cache/track3_checkpoints/wr_source_seed3710_step1600.pt
WR_RESUME_LOAD_ADAM=1
WR_RESUME_LOAD_OPTIMIZERS=0
WR_RESUME_RESTORE_RNG=1
WR_RESUME_ADVANCE_DATA=1
WR_TRAIN_STEPS=2125
WR_SCHEDULE_STEPS=3105
WR_SEED=3710
NPROC_PER_NODE=1
bash tools/prime_wr_record_resume_remote.sh
```

If the `1625/1750` points keep the hard-splice initial advantage without the
hard-splice flattening, extend the same pod to `2500` and then `3000`. If it
flattens by `1750`, stop; it is not the bridge.

## 2026-06-04 Handoff Probe Results

Provider/runtime:

```text
Prime Datacrunch H100 SXM5
pod: e3ba5d547a504c658ac556065772a8c2
logs: .opencode/prime_locom_handoff_20260604/
wallet before launch: $11.75
cleanup: pod terminated, Prime active pods = 0
```

The `env.local` key was valid once mapped as `PRIME_API_KEY=$PRIME_KEY`.

First, rebuilt the matched WR source step-1600 checkpoint on the same pod:

| run | result |
| --- | --- |
| `wr_source_state_seed3710_step1600_handoff` | `3.51918 @1600`, saved `/root/.cache/track3_checkpoints/wr_source_seed3710_step1600.pt` |

Then tested the LocoProp model checkpoint plus WR Adam-only state:

| run | LocoProp active after 1600? | 1625 | 1750 | read |
| --- | --- | ---: | ---: | --- |
| `wr_resume_locom1600_adamonly_seed3710` | no | `3.50208` | `3.50222` | preserves initial LocoProp-model advantage but immediately flattens |
| `wr_resume_locom1600_active_k4_cap020_seed3710` | yes, no gate | `3.50571` | stopped | worse immediately; accepted exploding local solves |
| `wr_resume_locom1600_active_gated_k4_cap020_seed3710` | yes, loss-decrease and cos gate | `3.50207` | `3.50218` | sane but still flat; mostly only shallow l0/l1 corrections accepted |

This answers the immediate question:

```text
LocoProp was not active in the Adam-only bridge suffix.
When turned on explicitly from 1600, no-gate harmed and gated was neutral.
```

The active no-gate diagnostics showed the same failure mode seen elsewhere:

```text
lossK >> loss0 in several deeper layers,
large correction norms,
norm cap rescales them,
but accepting those directions still worsens the first post-resume screen.
```

The gated run rejected those deep bad solves and applied mostly l0/l1
corrections. That avoided the immediate harm but did not fix the plateau:
`3.50207 -> 3.50218` from `1625` to `1750`.

Conclusion:

```text
The step-1600 LocoProp model state advantage is real enough to show up at 1625,
but the WR suffix with fresh Muon/SOAP state does not descend from it.
Adding LocoProp corrections after 1600 does not rescue this handoff.
The failure is optimizer-state/suffix geometry, not merely "LocoProp was off."
```
