# NanoGPT Optimizer Study: Right Metrics vs Soft-Muon

Status: working design doc.
Branch: `codex/wr-fresh-20260526`.
Latest pushed evidence commit: `b1388b0`.

## One-Sentence Summary

The current evidence says feature-derived right metrics are mechanically real
but not yet persistent enough, while no-C Soft-Muon has a real-looking
200-step signal that is currently confounded by the schedule-only split
optimizer path. The next useful experiment is separating singular-value
transfer from the explicit momentum-operand/polar-from-operand path.

## Scope

This document tracks optimizer interventions for the NanoGPT speedrun branch:

| family | mechanism | current status |
| --- | --- | --- |
| Diagonal feature Gram | per-coordinate input-energy scaling before/inside NorMuon | mostly noise or transient |
| Full feature Gram / Newton-Muon | right-precondition with `C = X^T X`, then Muon/polar | real early V signal, too slow and control-sensitive |
| Additive LocoProp-style correction | state-decoupled local `G f(C)` weight correction | structured but 80-step hits fade by 200 |
| No-C Soft-Muon | change Muon singular-value transfer without `C` | promising but path-confounded at 200 |

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

Study plot artifacts:

- `.opencode/optimizer_study_softmuon_200.svg`
- `.opencode/optimizer_study_softmuon_200_summary.md`

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

Completed PR291 compound 80-step screen:

| case | meaning | delta vs noop mean | read |
| --- | --- | ---: | --- |
| `mlpfc_sched` | path-only control for MLP c_fc | `-0.0018` | tiny path/noise positive |
| `mlpfc` | PR291 p=0.1 on MLP c_fc | `+0.0050` | failed |
| `all_l01` | PR291 p=0.1 on `qk,v,o,mlp_fc`, layers `0-1` | `-0.0067` | passed 80-step gate |

Interpretation: the PR291 polynomial did not reproduce the exact-eig MLP-only
hit. The broad surface run did pass, which makes the immediate hypothesis
surface coupling in the Muon bank, not MLP-local softening.

Current queued follow-up:

```text
runner: tools/run_softpolar_mlpfc_gate.sh
steps: 200
paired cases: noop, active, noop2
surfaces: qk,v,o,mlp_fc
layers: 0-1
implementation: PR291 p=0.1 polynomial Soft-Muon
```

Completed 200-step broad result:

| step | active | noop mean | delta | read |
| ---: | ---: | ---: | ---: | --- |
| 40 | `5.8676` | `5.8572` | `+0.0104` | worse |
| 80 | `5.1044` | `5.1117` | `-0.0073` | strong early win |
| 120 | `4.3914` | `4.3905` | `+0.0009` | parity/slightly worse |
| 160 | `4.0519` | `4.0518` | `+0.0001` | parity |
| 200 | `3.8836` | `3.8859` | `-0.0023` | beats both noops |

The broad PR291 polynomial result survives to 200, but with a small margin
against the best noop (`0.0008`). This is a positive optimizer signal, not a WR
claim.

Completed 200-step schedule-only broad control:

| step | active | noop mean | delta | read |
| ---: | ---: | ---: | ---: | --- |
| 40 | `5.8559` | `5.8674` | `-0.0115` | schedule path wins early |
| 80 | `5.0815` | `5.0949` | `-0.0134` | large mid-run win |
| 120 | `4.3943` | `4.3948` | `-0.0005` | parity/slightly better |
| 160 | `4.0511` | `4.0509` | `+0.0002` | parity |
| 200 | `3.8845` | `3.8866` | `-0.0021` | beats both noops |

Decision rule:

```text
Schedule-only beats both noops by roughly the same size as broad PR291
Soft-Muon. Therefore the broad PR291 200-step result is path-confounded.

The next test must isolate active singular-value transfer from the split path.
Run exact no-C Soft-Muon on the same broad surfaces/layers/window and compare
against the schedule-only row above.
```

Queued exact broad Soft-Muon:

```text
runner: tools/run_softpolar_mlpfc_gate.sh
steps: 200
surfaces: qk,v,o,mlp_fc
layers: 0-1
window: 48-64
implementation: exact eig Soft-Muon, alpha=0.9
diagnostic: LOCO_FULL_LOG_PRECOND=1
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
