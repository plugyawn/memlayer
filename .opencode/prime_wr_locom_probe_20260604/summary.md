# Prime WR+LocoProp-M Normalized Correction Probe, 2026-06-04

Platform: Prime Intellect B200 spot, pod `ab33db60b24a46b2a86625d8a0f235bf`, terminated after artifacts were pulled.

Wallet before this probe was `$43.62`; after cleanup it was `$42.71`. The pod cost was `$0.91`.

## Question

The earlier WR+LocoProp-M run with `inner_lr=1e-5` and local/cos gates was locally sane but applied raw corrections with norm around `1e-5`, far below the base Muon update. This probe tested whether the direction was useful if normalized to a meaningful fraction of the base step.

## Runs

| run | settings | validation |
| --- | --- | --- |
| `wr_locom_normbase_a025_k5_lr1e5_gated_250_seed3710_b200_v2` | `K=5`, `inner_lr=1e-5`, `sample_tokens=512`, `require_loss_decrease=1`, `min_cos=0.0`, `norm_to_base=1`, `norm_cap=0.20`, `alpha=0.25` | `4.53165 @125`, `4.05582 @250`, `2182ms/step` |
| `wr_locom_normbase_start50_cos005_a025_k5_lr1e5_125_seed3710_b200` | same, but `start_step=50`, `min_cos=0.05` | `4.52534 @125`, `2183ms/step` |

Reference points from the previous B200 WR probe:

| run | validation |
| --- | --- |
| WR source seed3710 | `4.52095 @125`, `4.05268 @250` |
| tiny gated LocoProp-M, raw scale | `4.51990 @125`, `4.05212 @250` |

## Read

The normalized correction did not rescue the WR+LocoProp path.

The first normalized run was worse than WR by `+0.01070` at step `125` and `+0.00314` at step `250`. The stricter start/cos gate improved the step-125 miss from `+0.01070` to `+0.00439`, but it was still behind the WR source.

The diagnostics explain the failure:

- The local objective can decrease while global alignment is weak. At step `125`, accepted logged cosines were only about `0.005-0.069` in the first normalized run.
- With `norm_to_base=1`, `norm_cap=0.20`, and `alpha=0.25`, the applied correction is about `5%` of the base Muon step. That is large enough to matter and it hurt.
- In the first normalized run, steps `0` and `1` applied nontrivial normalized corrections even though `grad=0`; `cos=0` passed the `min_cos=0` gate. Starting at step `50` and requiring `cos>=0.05` removed that blind early perturbation, but still did not beat WR.
- The implementation remains too slow for race work: about `2.18s/step` on B200 because the hook capture path disables `model.compile`.

## Current Diagnosis

LocoProp-M is not doing "nothing." The simple-Muon experiments showed a real mid-run model-state advantage. But the current additive hook implementation does not compose with the WR stack:

1. Suffixing a LocoProp model state into a mature WR optimizer state is not portable because the WR optimizer state is trajectory-dependent.
2. WR+LocoProp co-training through Python activation hooks is too slow.
3. Small locally sane corrections are too weak at raw scale.
4. Scaling locally sane corrections to a meaningful update size exposes weak global alignment and hurts.

So the current failure is not just late LR. It is update-map incompatibility plus a bad LocoProp insertion point/implementation.

## Better Way

Do not spend more Prime budget on hook-based WR+LocoProp sweeps.

The next plausible route is implementation-level:

1. Keep the WR substrate intact and compiled.
2. Add LocoProp-M as a first-class fused/current-path MLP correction, not Python hooks.
3. Gate corrections by meaningful global alignment, not only local loss decrease.
4. Apply a small schedule-aware correction only when its local/global diagnostics agree.

For the sub-3000 objective, the late tail likely has to come from the WR update-map machinery itself: PR287/power LR levels, MLP+V SOAP, Contra-to-normal by `2000`, Soft-Muon terminal ramp, and u/w floor behavior. The LocoProp prefix advantage around `2000-2200` cannot be converted by LR suffixing alone, and the hook-based additive correction is not clean enough to co-train with WR.
