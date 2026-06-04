# Prime Momscale Suffix Gate 2026-06-04

Purpose: test whether the recovered LocoProp-M step-2000 model state can be
made into a useful late suffix by pairing it with current-record WR optimizer
state, while varying optimizer-state trust.

Pod:

```text
id=8dd85bfb06a442f6a35e46e97e2697e9
name=oc-main-locom-momscale-h100stable-20260604-2212
gpu=1x H100_80GB SXM5 datacrunch
status=terminated, Prime pods total 0
wallet_after=$3.06
```

Local artifact:

```text
.opencode/prime_momscale_suffix_20260604/momscale_suffix_logs_20260604.tgz
sha256=fad4b3aef949ae39464d9b93f1f12c6612be98433171c0cc78000338fdf13600
```

## Builder

Built exact WR-source optimizer checkpoint at step 2000 on the same pod:

```text
checkpoint=/root/.cache/track3_checkpoints/wr_source_seed3710_step2000.pt
seed=3710
schedule_steps=3105
source=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt
generator_sha=334d608eb09d3b81ca9a838cf5eaaa9fe2daa62ffe73cf6cfea5a2626dec92fe
```

Builder trajectory:

```text
125:  4.52482
250:  4.05574
500:  3.82550
1000: 3.65353
1500: 3.53793
1750: 3.48854
1875: 3.46206
2000: 3.43525
```

## Suffix Tests

Both suffixes started from:

```text
model_checkpoint=/root/.cache/track3_checkpoints/track3_prime_recover_loco2400_h3075ramp2350x150_seed3710_step2000.pt
start_loss=3.38827 @2000
```

### Mature WR Optimizer State, Optimizer2 Momentum Scale 0.5

```text
optimizer_checkpoint=/root/.cache/track3_checkpoints/wr_source_seed3710_step2000.pt
WR_RESUME_LOAD_OPTIMIZERS=1
WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE=0.5
scaled_momentum=72

2000: 3.38827
2125: 3.43293
2250: 3.41426
2375: 3.39274
```

The line partially recovered but was still worse than the starting loss by
2375. This is not a hot suffix.

### Fresh WR Optimizer State

```text
WR_RESUME_LOAD_OPTIMIZERS=0

2000: 3.38827
2125: 3.43373
```

This also shocked upward, and was killed.

## Takeaway

The problem is not solved by simply importing less WR optimizer2 momentum or by
using fresh WR state. The recovered LocoProp model state is not compatible with
the current-record WR suffix dynamics in this direct splice form. The good
mid-run LocoProp state needs a schedule/state path that preserves its own
dynamics, not a hard transition into WR optimizer state.

