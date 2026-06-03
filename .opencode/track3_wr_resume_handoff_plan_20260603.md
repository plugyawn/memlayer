# Track 3 LocoProp-M -> WR Tail Handoff Plan, 2026-06-03

## Objective

Find the first credible example where LocoProp-M helps a Track 3 run reach
`3.28` before step `3000`.

The current best LocoProp-M scheduler-only lanes did not land:

```text
best h3075/ramp lane:        3.30262 @3000
best smooth WR-LR blend:     3.29892 @3000
WR source mean/reference:    3.28096 @3000
record h3075 mean/reference: 3.28106 @3000
```

## Current Diagnosis

The old scheduler-only experiments prove that the LocoProp prefix can create a
better mid-run state, but they also show that the simple-Muon suffix lacks the
WR update map.

Measured drops:

```text
WR source mean:
  2000 -> 2500: 0.09142
  2500 -> 3000: 0.06281
  2000 -> 3000: 0.15423

best smooth LocoProp suffixes:
  2000 -> 2500: about 0.060-0.061
  2500 -> 3000: about 0.059-0.061
  2000 -> 3000: about 0.120

old cd500 -> softmerge p1.10:
  2000 -> 2500: 0.08440
  2500 -> 3000: 0.03195
  2000 -> 3000: 0.11635
```

So the failure is not only "LR too cold." Some suffixes have acceptable terminal
slope but are too weak in `2000->2500`; others get a strong mid-run drop and
then lose terminal slope. The WR source gets both through optimizer geometry:
SOAP on MLP+V, Contra-to-normal transition, Soft-Muon terminal transition,
update floor/clamp behavior, and PR287-style power LR.

## Why The Previous WR+LocoProp Probe Failed

The direct current-record WR+LocoProp-M integration inserted activation capture
hooks into the WR source. On the Prime GH200, every runnable variant OOMed
before step `0` backward, including a layers `0-3` capture attempt.

That is an implementation/memory failure, not an algorithmic result.

## New Probe

Test a model-state handoff instead:

```text
prefix: simple Track 3 + LocoProp-M to step 1600
checkpoint: track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
suffix: current-record WR source, no LocoProp hooks
state: load model, restore RNG/data stream, initialize WR optimizer stack fresh
```

This directly tests whether LocoProp-M created a better prefix state that the
WR late optimizer can land.

Tooling added:

```text
tools/make_wr_record_resume.py
tools/run_wr_record_resume.sh
tools/prime_wr_record_resume_remote.sh
```

Dry generation/compile passed locally:

```text
WR_RESUME_DRY_RUN=1 WR_RESUME_GENERATED_SCRIPT=/tmp/train_gpt_wr_record_resume_dry.py \
WR_TRAIN_STEPS=3040 WR_SCHEDULE_STEPS=3105 bash tools/run_wr_record_resume.sh
```

## Launch Command

Once an H100/GH200 is allocatable on Prime, sync the repo and checkpoint, then
run:

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

## Gates

Stop or branch quickly if:

```text
1625 has a large resume spike or model-key mismatch
2000 is worse than about 3.42
2500 is worse than about 3.34
```

Promote if:

```text
it reaches <= 3.28 before 3000
or the 2000->3000 slope is >= 0.145 with a LocoProp-improved entry state
```

If model-only resume spikes but keys match, next variant is:

```text
WR_RESUME_LOAD_ADAM=1
```

This preserves Adam moments for embedding/proj/bias while still initializing
the WR Muon/SOAP state fresh.

## Prime Status

Prime wallet was readable and showed `$47.28`.

Active pods before launch attempts:

```text
none
```

Launch attempts:

```text
GH200 96GB @ $1.99/hr, id 5ba376: provider HTTP 400, no pod allocated
H100 80GB @ $2.35/hr, id 6bd7c8: no valid GPU configuration found
GH200 via cloud id vbm-72c-480gb-gh200-gpu: provider HTTP 400, no pod allocated
```

No active Prime pod remains and no workload was started.
