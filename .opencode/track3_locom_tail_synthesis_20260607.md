# Track 3 LocoProp-M Tail Synthesis 2026-06-07

## Provenance

- Pod: `43ad3702f6e843d397f1e5e2d1d6dbb1`
- GPU: `NVIDIA H100 80GB HBM3` SXM/datacrunch spot
- Remote repo: `/root/wr-track3-locom-20260606`
- Pinned stack: `torch 2.7.1+cu126`, `triton 3.3.1`, `numpy 2.2.6`
- Root checkpoint:
  `/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- Root checkpoint SHA256:
  `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`

The step-1600 checkpoint resume was verified by the expected first screen:

```text
track3_checkpoint_loaded ... step:1600 seed:3710 load_optimizers:True
step:1600 ... val_loss:3.48241
```

## Recreated Branch Points

The good prefix was replayed checkpoint-natively to create a clean step-2000
state:

```text
1875: 3.38820
1900: 3.38478
1925: 3.38175
1950: 3.37911
1975: 3.37605
```

The produced step-2000 checkpoint is:

```text
/root/.cache/track3_checkpoints/track3_locom_good2000_tailcopy43ad37_seed3710_step2000.pt
SHA256: 53ee13b38d5b3f12279d02031fc1100c0c2467c2fc56daf34af642f750f4577b
```

The cold continuation from the step-2000 checkpoint produced a clean step-2500
branch point:

```text
2500: 3.34114
```

## Tail Results

### Cold Tail From 2500

No LocoProp, cold power tail to 3000:

```text
2500: 3.34114
2600: 3.33827
2750: 3.33560
2800: 3.33513
2875: 3.33472
3000: 3.33457
```

This is the core failure mode: by the real terminal region the trajectory is
almost flat. From 2875 to 3000 it drops only about `0.00015`.

### Terminal SoftMuon From 2500

Settings:

```text
TRACK3_SOFT_MUON=1
TRACK3_SOFT_MUON_BLEND=1.0
TRACK3_SOFT_MUON_START_STEP=2500
TRACK3_SOFT_MUON_END_STEP=3010
TRACK3_SOFT_MUON_CEIL=0.80
TRACK3_SOFT_MUON_NORM_RESTORE=1
```

Result:

```text
2500: 3.34114
2600: 3.33829
2750: 3.33562
2800: 3.33513
2875: 3.33472
3000: 3.33453
```

Terminal SoftMuon did not rescue the tail. It is essentially tied with the cold
tail at every screen.

### LocoProp Re-On From 2500, Ungated, 0.05x

Settings:

```text
TRACK3_LOCOM_ENABLED=1
TRACK3_LOCOM_ACTIVE_WINDOWS=2500:2600
TRACK3_LOCOM_STEPS=5
TRACK3_LOCOM_INNER_LR=2e-4
TRACK3_LOCOM_TARGET_SPACE=post
TRACK3_LOCOM_TRUE_POST_GRAD=1
TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=0
TRACK3_LOCOM_MIN_COS_DESC=-inf
TRACK3_LOCOM_NORM_TARGET=0.05
TRACK3_LOCOM_NORM_CAP=0.20
TRACK3_LOCOM_CORRECTION_MODE=normal
```

Result:

```text
2525: 3.34036
2550: 3.33962
2575: 3.33891
2600: 3.33829
```

This also tied the cold tail. The correction was not discarded:

```text
step 2500 eff_frac_med=0.05
step 2525 eff_frac_med=0.05
step 2550 eff_frac_med=0.05
step 2575 eff_frac_med=0.05
```

So the failure is not just that the gate erased LocoProp or the cap made it too
small. A deliberately applied 5 percent base-step correction still did not move
the validation curve.

### LocoProp Re-On From 2500, Softpolar, 0.05x

Same as above, except:

```text
TRACK3_LOCOM_CORRECTION_MODE=softpolar
```

Result:

```text
2525: 3.34037
2550: 3.33963
2575: 3.33892
2600: 3.33830
```

Softpolar shaping did not help. The applied effective norm was still 0.05x, but
the raw softpolar correction was enormous and scaled down:

```text
step 2500 raw_frac_med=680.6, eff_frac_med=0.05
step 2525 raw_frac_med=734.7, eff_frac_med=0.05
step 2550 raw_frac_med=805.0, eff_frac_med=0.05
step 2575 raw_frac_med=918.6, eff_frac_med=0.05
```

That makes softpolar-on-correction a poor explanation for the missing tail.

## Current Read

1. The good prefix is real enough to recreate, but the suffix cannot be fixed by
   simply keeping the same cold schedule.
2. The terminal failure is not a simple LR-floor problem. Floors and hotter
   horizons worsened earlier in this run family.
3. Normal LocoProp re-on at 2500 does not help, even when ungated and applied at
   a material 5 percent base-step norm.
4. Softpolar/polar-style shaping of the LocoProp correction also does not help
   from the flat 2500 state.
5. The local objective can improve while the global validation curve remains
   unchanged. The LocoProp correction is not presently aligned with the suffix
   descent geometry in a way that survives validation.

## What Would Make LocoProp Tick

The missing ingredient is not more local SGD steps by itself, nor a larger norm
cap by itself. The correction needs at least one of:

- a target residual that aligns with actual suffix descent rather than the local
  sampled matching objective;
- a surface/layer subset whose correction has a reliable validation effect;
- a state where the Muon/optimizer trajectory is still receptive to this
  correction, likely earlier than the 2500 flat state;
- a different optimizer-state bridge that preserves the prefix advantage without
  entering the cold flat tail.

Given the current evidence, the LocoProp-M correction is a prefix/trajectory
phenomenon, not a reliable late-tail rescue primitive in this implementation.

## Local Artifacts

```text
.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/cold2500_to3000/
.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/soft2500_to3000/
.opencode/current_track3_ledger_20260607_logs/tailcopy_43ad37/tail2500_tick/
.opencode/prime_scripts/run_prime_track3_locom_tail2500_tick.sh
```
