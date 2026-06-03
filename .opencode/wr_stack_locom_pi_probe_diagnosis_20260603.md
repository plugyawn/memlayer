# WR Stack + LocoProp-M PI Probe Diagnosis, 2026-06-03

## Objective

Use the remaining Prime Intellect budget to test whether the current Track 3 WR stack can preserve the simple-Muon + LocoProp-M mid-run advantage around steps 2000-2200 and turn it into a sub-3000 landing.

## Active GPU

- Prime pod: `6d73b2cff0624ce2a3fff0eb0c60ccfd`
- GPU: 1x GH200, reported as `NVIDIA GH200 480GB` with 94.50 GiB visible HBM
- Price: 2.29 USD/hr
- Status: terminated after evidence collection
- Active pods after cleanup: 0

## What Actually Happened

This did not produce a loss curve. Every runnable WR+LocoProp attempt failed before step 0 in backward.

Evidence archive:

```text
.opencode/prime_wr_locom_probe_20260603/wr_record_locom_probe_20260603.tgz
```

Important failures:

```text
v6 uncompiled all-layer capture:
  CUDA OOM before step 0
  allocated 90.26 GiB, tried to allocate another 12.28 GiB

v7/v8/v9 compiled all-layer capture:
  torch._dynamo recompile_limit hit on hook/capture path
  CUDA OOM before step 0
  allocated 82.91 GiB, only about 10.28 GiB free, tried another 12.28 GiB

v10 MLP capture uncompiled:
  CUDA OOM before step 0
  same 82.91 GiB allocated / 12.28 GiB requested pattern

v11 only layers 0-3 on capture path:
  CUDA OOM before step 0
  same 82.91 GiB allocated / 12.28 GiB requested pattern
```

The data-cache issue was separate and is fixed for future Prime probes:

```text
HF Xet path stalled on Prime after a few shards.
HF_HUB_DISABLE_XET=1 downloaded shards 5-16 in seconds.
The launcher now derives required FineWeb shard count from train steps.
```

Relevant pushed commits:

```text
041b055 Speed up Prime HF shard caching
716c8fa Derive Prime FineWeb shard count from steps
c31b97c Run WR LocoProp generator via bash
d2682de Keep WR LocoProp capture out of Dynamo
f50665f Allow layer index through WR LocoProp compile
e2944dd Keep WR LocoProp MLP capture uncompiled
5bd09bf Compile inactive WR LocoProp MLP layers
```

## Diagnosis

The current hook-based WR-source LocoProp-M integration is the wrong implementation for the WR stack.

The simple-Muon LocoProp-M runs worked because that script had enough memory headroom and did not depend on the exact current-record compile shape. The 2026-05-09 WR stack is already close to the memory edge. Adding activation hooks and Python capture inside the MLP path breaks the compiled memory plan, and the model cannot even finish the first backward on this GH200.

This explains why the existing suffix experiments were misleading:

- The earlier LocoProp-M/schedule lines had a real mid-run benefit.
- But those lines were not using the full current WR late optimizer stack.
- When trying to compose with the real WR stack, the current capture implementation is not runnable, so no conclusion about algorithmic composition can be drawn from this Prime probe.

## What Is Going Wrong Algorithmically In The Existing Curves

From the pre-existing TSV slope comparison:

```text
WR source mean:
  2000 -> 2500 drop 0.09142
  2750 -> 3000 drop 0.02558

live smooth blend suffixes:
  2000 -> 2500 drop about 0.060-0.061
  2750 -> 3000 drop about 0.0249

h3075+ramp suffix:
  1600 -> 2000 drop 0.08929
  2750 -> 3000 drop 0.01792
```

So the failure is not simply "late LR too low."

The smooth suffixes keep acceptable terminal slope but are too weak in 2000-2500. The h3075+ramp suffix gets the 1600-2000 punch but then loses terminal slope. The actual WR stack gets both via optimizer geometry, not just LR:

- SOAP/MLP and SOAP/V style preconditioning
- Contra-to-normal transition
- Soft-Muon transition near the terminal phase
- update clamp/floor machinery
- PR287-style power LR levels

## Better Way

Do not spend more GPU on hook-based LocoProp capture in the WR source.

The next viable implementation is to add LocoProp-M as a first-class fused/local MLP primitive, not as Python hooks:

1. Replace MLP with a custom autograd function or fused module that returns the same forward output and emits sampled `(x, post, dpre)` from backward without retaining extra full activation tensors or forcing Dynamo graph churn.
2. Keep `model.compile(dynamic=False)` for the WR graph.
3. Apply the additive LocoProp correction after the WR optimizer step, state-decoupled as before.
4. Start with a narrow active window and layer set only after the capture path proves it can run step 0 on 1x GPU.

Immediate low-cost validation ladder:

```text
1. Local/remote dry generation and py_compile.
2. 1x GPU step-0 backward smoke with WR_LOCOM_ENABLED=1, compile on.
3. 125-step curve only if step-0 fits.
4. 2000-2200 probe only if 125/250 are not worse than WR source.
```

If we want a quick schedule-only win from the old LocoProp curves without more implementation work, the best hypothesis is still:

```text
early/mid simple-Muon + LocoProp-M prefix
then real WR optimizer geometry for the tail
```

But that requires a compatible checkpoint/state handoff between the simple script and the WR source, which is not currently established. A scheduler-only handoff is not enough; the WR stack's late geometry is materially different.
