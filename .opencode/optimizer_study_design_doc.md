# NanoGPT Optimizer Study: Right Metrics vs Soft-Muon

Status: working design doc.
Branch: `codex/wr-fresh-20260526`.
Latest pushed evidence commit: `70cda3f`.

## One-Sentence Summary

The current evidence says feature-derived right metrics are mechanically real
but not yet persistent enough, while no-C Soft-Muon singular-value transfer has
the cleanest recent paired 200-step signal and should be promoted before more
feature-Gram plumbing.

## Scope

This document tracks optimizer interventions for the NanoGPT speedrun branch:

| family | mechanism | current status |
| --- | --- | --- |
| Diagonal feature Gram | per-coordinate input-energy scaling before/inside NorMuon | mostly noise or transient |
| Full feature Gram / Newton-Muon | right-precondition with `C = X^T X`, then Muon/polar | real early V signal, too slow and control-sensitive |
| Additive LocoProp-style correction | state-decoupled local `G f(C)` weight correction | structured but 80-step hits fade by 200 |
| No-C Soft-Muon | change Muon singular-value transfer without `C` | best recent 200-step paired control |

Non-goals for this branch right now:

- Full `3072 x 3072` MLP projection feature matrices.
- Uncontrolled PR-claim reproduction without paired noops.
- Combining feature C, SOAP, contra-Muon, and Soft-Muon before isolating each.

## Current Compute Graph

Baseline NorMuon path:

```text
raw reduced gradient
  -> Nesterov momentum operand
  -> Polar Express / matrix-sign approximation
  -> NorMuon variance reduction
  -> cautious weight decay and parameter update
```

Feature-C Newton-Muon path tested:

```text
raw gradient or momentum operand
  -> right metric from feature Gram C
  -> Polar Express
  -> NorMuon variance reduction
  -> update
```

No-C Soft-Muon path now tested:

```text
raw gradient
  -> Nesterov momentum operand
  -> hard Polar Express baseline
  -> soft singular-value transfer on same operand
  -> norm-restored blend into hard update
  -> NorMuon variance reduction
  -> update
```

## Evidence So Far

### Feature C / LocoProp-style correction

MLP `c_fc` natural-cap20 additive correction initially passed an 80-step
screen, but failed the 200-step promotion:

| run | active | noop1 | noop2 | noop mean | delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| MLP c_fc cap20 at 200 | `3.8876` | `3.8850` | `3.8843` | `3.8846` | `+0.0030` |

Interpretation: the right-metric direction is nontrivial, but this trust rule
does not produce durable 200-step improvement.

### No-C Soft-Muon exact alpha0.9

Artifacts:

- `.opencode/modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch.log`
- `.opencode/modal_softmuon_noc_mlpfc_a09_200_h100_20260531.summary.md`
- `.opencode/modal_softmuon_noc_mlpfc_a09_200_h100_20260531.loss.svg`

MLP `c_fc`, layers `0-1`, window `48-64`, exact spectral transfer
`alpha=0.9` (`p ~= 0.1`):

| step | active | noop1 | noop2 | noop mean | delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 40 | `5.8661` | `5.8724` | `5.8851` | `5.8788` | `-0.0126` |
| 80 | `5.0898` | `5.1156` | `5.1175` | `5.1166` | `-0.0268` |
| 120 | `4.3825` | `4.3911` | `4.3843` | `4.3877` | `-0.0052` |
| 160 | `4.0497` | `4.0510` | `4.0501` | `4.0506` | `-0.0008` |
| 200 | `3.8840` | `3.8854` | `3.8859` | `3.8857` | `-0.0017` |

Diagnostic at full blend:

```text
step 64: delta=0.1842, cos=0.982980
```

Interpretation: the effect is large near the intervention and small but
positive at 200. It does not involve feature Gram collection. This makes
Soft-Muon singular-value transfer the top immediate branch.

## Implementation Contract

Soft-Muon toggles:

| env var | values | meaning |
| --- | --- | --- |
| `LOCO_SOFT_POLAR` | `0/1` | enable isolated no-C Soft-Muon probe |
| `LOCO_SOFT_POLAR_SURFACES` | `qk,v,o,mlp_fc` subset | matrix-bank surfaces touched |
| `LOCO_SOFT_POLAR_IMPL` | `exact`, `pr291` | exact eig transfer or PR291 p=0.1 polynomial |
| `LOCO_SOFT_POLAR_ALPHA` | `[0,1]` | exact eig exponent, with `p = 1 - alpha` |
| `LOCO_SOFT_POLAR_POWER` | currently `0.1` for PR291 | PR291 singular-value power |
| `LOCO_SOFT_POLAR_SCHEDULE_ONLY` | `0/1` | split-path control with zero soft update |
| `LOCO_SOFT_POLAR_WINDOWS` | step ranges | active window |

Implementation files:

| file | role |
| --- | --- |
| `train_gpt.py` | optimizer toggles, exact eig path, PR291 polynomial path, schedule-only path |
| `tools/run_softpolar_mlpfc_gate.sh` | single Soft-Muon paired screen runner |
| `tools/run_softpolar_pr291_two_screen.sh` | compound PR291 schedule-only / MLP / broad screen |
| `tools/summarize_paired_cases.py` | paired active-vs-noop summary |
| `tools/plot_paired_losses_svg.py` | dependency-free paired loss SVG plots |

## Next Experiment

Queued after H100 meditation:

```text
runner: tools/run_softpolar_pr291_two_screen.sh
steps: 80
paired cases: noop, active, noop2
cases:
  1. mlpfc_sched: schedule-only split path, zero soft update
  2. mlpfc: PR291 p=0.1 polynomial on MLP c_fc
  3. all_l01: PR291 p=0.1 polynomial on qk,v,o,mlp_fc layers 0-1
```

Decision rule:

```text
If mlpfc_sched wins, treat the exact alpha0.9 result as path-confounded.
If mlpfc active wins but broad loses, keep Soft-Muon narrow and promote to 200.
If broad wins at 80, run broad PR291 200-step paired before returning to C.
If all PR291 polynomial cases lose, exact eig alpha0.9 was not a faithful
PR291 adaptation; retest exact broad or drop back to feature-C diagnostics.
```

## Open Risks

- Exact eig alpha0.9 is not the PR291 implementation; it is only a clean
  spectral-transfer control.
- PR291 combines Soft-Muon with SOAP, contra-Muon, u/w-floor changes, and a
  late schedule. The current branch intentionally isolates only Soft-Muon.
- The current best no-C win is still small at 200 (`-0.0017`), so it is not
  enough for a WR claim without broader/persistent evidence.
- If feature C is revisited, future-alignment diagnostics should be added
  before another broad scalar sweep.
