# Track 3 LocoProp-M Runbook

This branch contains the Track 3 LocoProp-M experiment harness used for the
recent optimizer-schedule sweeps. It is experimental code, not a record claim.
The latest plotted tail comparison ends with the best new lane at
`3.30262 @3000`, well outside the current WR/reference band.

Latest plot artifacts:

- `.opencode/plots/track3_oldtail_vs_live_blends_20260603_refresh3_full.png`
- `.opencode/plots/track3_oldtail_vs_live_blends_20260603_refresh3_midlate.png`
- `.opencode/plots/track3_oldtail_vs_live_blends_20260603_refresh3_terminal.png`
- `.opencode/plots/track3_oldtail_vs_live_blends_20260603_refresh3.tsv`

## What The Harness Does

`tools/make_track3_locoprop_m.py` generates a Track 3 training script from
`train_gpt.py` and adds:

- MLP `c_fc` LocoProp-M local correction probes.
- optional hookless auxiliary capture (`TRACK3_LOCOM_AUX_CAPTURE=1`) so the real
  training forward/backward can stay compiled while LocoProp samples are
  collected in a small explicit aux pass.
- optional batched local preparation (`TRACK3_LOCOM_BATCHED_PREP=1`) for the
  standard SGD local solve, stacking owned MLP layers and running the K local
  steps with batched GEMMs.
- Norm-capped additive correction application.
- checkpoint save/resume with optimizer/RNG restore controls.
- linear, power, PR287-style, blended, and temporary LR-bump schedules.
- optional Soft-Muon ramp for late-stage suffix tests.
- diagnostics for correction norms, loss decrease, and descent cosine.

`tools/run_track3_locoprop_m.sh` is the local runner. It prints source,
generator, and generated-script SHA256 hashes before training so checkpoint
provenance can be reconstructed.

## Local 1x Run

Install the normal repo requirements and cache FineWeb as usual:

```bash
pip install -r requirements.txt
python data/cached_fineweb10B.py 9
```

Then run a 1x Track 3 LocoProp-M screen:

```bash
TRACK3_TRAIN_STEPS=3000 \
TRACK3_NUM_TRIALS=1 \
TRACK3_SEED_OFFSET=3710 \
TRACK3_LOCOM_ENABLED=1 \
TRACK3_LOCOM_LAYERS=all \
TRACK3_LOCOM_STEPS=4 \
TRACK3_LOCOM_NORM_CAP=0.20 \
TRACK3_LOCOM_AUX_CAPTURE=1 \
TRACK3_LOCOM_AUX_SEQS=16 \
TRACK3_LOCOM_BATCHED_PREP=1 \
SCREEN_VAL_EVERY=25 \
bash tools/run_track3_locoprop_m.sh
```

Use `TRACK3_DRY_RUN=1` to only generate and compile-check the script.

The legacy capture path uses Python activation/backward hooks on the final
microbatch, which forces the active microbatch through the uncompiled model. Use
`TRACK3_LOCOM_AUX_CAPTURE=1` for timing-sensitive probes: the generated script
keeps all normal training microbatches on the compiled model, then runs a small
manual aux forward on `TRACK3_LOCOM_AUX_SEQS` sampled sequences to populate the
same LocoProp sample buffers. This is the fast path; set
`TRACK3_LOCOM_AUX_CAPTURE=0` only when you explicitly want the old hook-control
semantics.

For the usual `local_opt=sgd`, `target_space=post`, 1x-H100 screen, add
`TRACK3_LOCOM_BATCHED_PREP=1`. This preserves the same local K-step update but
computes all owned MLP `c_fc` corrections in a stacked tensor path. It currently
falls back before consuming samples for unsupported modes such as RMSProp or
multi-rank sample gathering.

## Modal Single-Lane Run

For Modal, use the launcher wrapper. Keep the protobuf env var; it avoids local
Modal CLI descriptor failures on this machine.

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
MODAL_DETACH=1 \
NANOGPT_MODAL_GPU=H100 \
MODAL_RUN_NAME=track3-locom-screen-seed3710 \
TRACK3_TRAIN_STEPS=3000 \
TRACK3_SEED_OFFSET=3710 \
SCREEN_VAL_EVERY=25 \
bash tools/launch_modal_track3_locom_3000_seed.sh
```

For the current fused timing screen, prefer the dedicated wrapper:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
MODAL_DETACH=1 \
NANOGPT_MODAL_GPU=H100 \
TRACK3_TRAIN_STEPS=500 \
TRACK3_SEED_OFFSET=3710 \
TRACK3_MBS=64 \
TRACK3_LOCOM_AUX_CAPTURE=1 \
TRACK3_LOCOM_AUX_SEQS=16 \
TRACK3_LOCOM_BATCHED_PREP=1 \
SCREEN_VAL_EVERY=125 \
bash tools/launch_modal_track3_locom_fused_screen.sh
```

Use a dry run to verify the generated path without touching GPU quota:

```bash
TRACK3_DRY_RUN=1 bash tools/launch_modal_track3_locom_fused_screen.sh
```

Parse logs with:

```bash
python3 tools/parse_track3_locom_log.py /path/to/run.log
```

The parser reports final validation loss, recent non-eval step time, whether
`aux_capture`/`batched_prep` were requested, and whether `batched=1` appeared in
the LocoProp diagnostics.

## WR-Current-Record Fast Path

For probes on the checked-in current-record source, prefer the hookless aux
generator. The runner defaults to `WR_LOCOM_GENERATOR=aux` and now requests
batched prep by default for that generator:

```bash
WR_LOCOM_GENERATOR=aux \
WR_LOCOM_BATCHED_PREP=1 \
WR_LOCOM_AUX_SEQS=16 \
WR_TRAIN_STEPS=3040 \
WR_SCHEDULE_STEPS=3105 \
bash tools/run_wr_record_locoprop_m.sh
```

This keeps the main WR training path compiled, collects LocoProp samples through
a small explicit aux forward/autograd pass, and runs the per-layer K-step local
SGD solve as stacked batched GEMMs. Set `WR_LOCOM_GENERATOR=hook` only for a
legacy hook-control run.

## Resume From A 1600-Step Checkpoint

The recent suffix tests resumed from a 1600 checkpoint and preserved model,
optimizer, RNG, and data-stream provenance. The checkpoint path must exist on
the Modal/remote machine:

```bash
export TRACK3_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
export TRACK3_RESUME_ADVANCE_DATA=1
export TRACK3_RESUME_RESTORE_RNG=1
export TRACK3_RESUME_LOAD_OPTIMIZERS=1
export TRACK3_SEED_OFFSET=3710
export TRACK3_TRAIN_STEPS=3000
export TRACK3_CHECKPOINT_STEPS=2000,2400
export TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints
export TRACK3_CHECKPOINT_PREFIX=track3_loco2400_h3075ramp2350x150

PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
MODAL_DETACH=1 \
NANOGPT_MODAL_GPU=H100 \
MODAL_RUN_NAME=track3-redckpt1600-loco2400-h3075ramp2350x150 \
TRACK3_LOCOM_ACTIVE_WINDOWS=0:1800,2400:3000 \
TRACK3_LOCOM_END_STEP=3000 \
TRACK3_LR_BLEND_START=1800 \
TRACK3_LR_BLEND_END=2000 \
TRACK3_LR_BLEND_TARGET=pr287 \
TRACK3_LR_BLEND_TARGET_POWER=1.10 \
TRACK3_LR_BLEND_TARGET_STEPS=3075 \
TRACK3_LR_BUMP_WINDOWS=2350:2600:3000:3000:1.50 \
bash tools/launch_modal_track3_locom_3000_seed.sh
```

That exact family is the one plotted in the refresh3 artifacts. It did not land
near the WR tail, but it is useful as a reproducible negative control.

## Fanout Helpers

The helper scripts below launch small suffix grids. They assume the checkpoint
path exists on the remote host or Modal volume.

```bash
bash tools/launch_modal_track3_locom_cd500_suffix_array.sh
bash tools/launch_modal_track3_locom_resume1600_lr_array.sh
bash tools/launch_modal_track3_locom_blend_tail3.sh
```

## Important Env Knobs

Core LocoProp-M:

```text
TRACK3_LOCOM_ENABLED=1
TRACK3_LOCOM_LAYERS=all
TRACK3_LOCOM_STEPS=4
TRACK3_LOCOM_NORM_CAP=0.20
TRACK3_LOCOM_AUX_CAPTURE=1
TRACK3_LOCOM_AUX_SEQS=16
TRACK3_LOCOM_BATCHED_PREP=1
TRACK3_LOCOM_ACTIVE_WINDOWS=0:1800
TRACK3_LOCOM_END_STEP=1800
```

Schedule controls:

```text
TRACK3_LR_SCHEDULE=linear|power|pr287
TRACK3_LR_POWER=1.0
TRACK3_LR_SCHEDULE_STEPS=3000
TRACK3_LR_BLEND_START=1800
TRACK3_LR_BLEND_END=2000
TRACK3_LR_BLEND_TARGET=pr287
TRACK3_LR_BLEND_TARGET_POWER=1.10
TRACK3_LR_BLEND_TARGET_STEPS=3075
TRACK3_LR_BUMP_WINDOWS=start:ramp_end:hold_end:fade_end:mult
```

Checkpoint controls:

```text
TRACK3_CHECKPOINT_STEPS=1600,2000,2400
TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints
TRACK3_RESUME_CHECKPOINT=/path/to/checkpoint.pt
TRACK3_RESUME_LOAD_OPTIMIZERS=1
TRACK3_RESUME_RESTORE_RNG=1
TRACK3_RESUME_ADVANCE_DATA=1
```

Soft-Muon suffix controls:

```text
TRACK3_SOFT_MUON=1
TRACK3_SOFT_MUON_BLEND=1.0
TRACK3_SOFT_MUON_START_STEP=2500
TRACK3_SOFT_MUON_END_STEP=3010
TRACK3_SOFT_MUON_CEIL=0.80
```

## Current Read

The strongest current evidence is that LocoProp-M creates real early/mid-run
loss improvements, but the later handoff/suffix has not preserved those gains.
The refresh3 plot shows the failure mode clearly: the LocoProp suffixes cluster
around `3.302-3.306 @3000`, while the WR/reference means continue descending to
about `3.281 @3000`.

## Current Next Probe

The direct current-record WR + LocoProp-M hook integration OOMed before step 0
on Prime. The next probe is therefore a model-state handoff:

```text
simple Track 3 + LocoProp-M prefix checkpoint at step 1600
-> current-record WR source suffix with no LocoProp hooks
```

Use:

```bash
WR_RESUME_DRY_RUN=1 bash tools/run_wr_record_resume.sh
```

for local generation/compile, and:

```bash
RUN_LABEL=wr_resume_locom1600_modelonly_seed3710 \
WR_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt \
WR_RESUME_LOAD_ADAM=0 \
WR_RESUME_RESTORE_RNG=1 \
WR_RESUME_ADVANCE_DATA=1 \
WR_TRAIN_STEPS=3040 \
WR_SCHEDULE_STEPS=3105 \
WR_SEED=3710 \
WR_TARGET_LOSS=3.28 \
NPROC_PER_NODE=1 \
bash tools/prime_wr_record_resume_remote.sh
```

on a synced Prime H100/GH200 pod. The rationale and launch gates are recorded
in `.opencode/track3_wr_resume_handoff_plan_20260603.md`.
