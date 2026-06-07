# Track 3 c_proj LocoProp Specificity Result

Date: 2026-06-07

## Remote

- Provider: Prime Intellect
- Pod: `45a63f7f45a5471fa42669792d146237`
- GPU: `NVIDIA H100 80GB HBM3`
- Price: `$1.138/hr` spot
- Status: terminated after artifact pull; Prime active pods returned zero.

## Provenance

- Local checkpoint copied first:
  `/Users/progyan/speedrun/tmp/modal_ckpt_transfer/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- Remote checkpoint:
  `/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt`
- SHA256:
  `430dc1d871ad177e9675679174d5ee84d3f02e6ebdf8aba6bec72093210debf2`
- Remote stack:
  `torch 2.7.1+cu126`, `triton 3.3.1`
- Data cache:
  `python data/cached_fineweb10B.py 20`, 21 bin files.

## Experiment

Runner:

```bash
MODE=pair \
TRACK3_PROJ_SPEC_LOG_DIR=/root/prime_track3_locom_proj_specificity_logs_retry \
TRACK3_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt \
TRACK3_TRAIN_STEPS=2000 \
TRACK3_PREFIX_ACTIVE_END=1800 \
TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
TRACK3_LOCOM_STEPS=5 \
TRACK3_LOCOM_INNER_LR=2e-4 \
bash tools/run_track3_locom_proj_specificity.sh
```

The first attempt failed before data cache with `RuntimeError: generator raised StopIteration`.
After FineWeb cache setup, the run loaded the checkpoint correctly:

```text
track3_checkpoint_loaded ... step:1600 seed:3710 load_optimizers:True
track3_resume_advanced_data steps:1600
```

## Result

The active `c_proj` K5 correction matched alpha-zero. The active lane was stopped
at 1800 because it missed the materiality gate by a wide margin.

| step | active | alpha_zero | control-active |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48241 | 3.48241 | 0.00000 |
| 1625 | 3.45135 | 3.45137 | 0.00002 |
| 1650 | 3.43561 | 3.43561 | 0.00000 |
| 1675 | 3.42615 | 3.42614 | -0.00001 |
| 1700 | 3.41883 | 3.41882 | -0.00001 |
| 1725 | 3.41288 | 3.41290 | 0.00002 |
| 1750 | 3.40794 | 3.40794 | 0.00000 |
| 1775 | 3.40360 | 3.40361 | 0.00001 |
| 1800 | 3.39870 | 3.39872 | 0.00002 |

Gate read: active matches alpha-zero.

## Artifacts

- Archive:
  `.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/prime_track3_locom_proj_specificity_logs_retry.tgz`
- Decision report:
  `.opencode/current_track3_ledger_20260607_logs/proj_specificity_45a63/proj_specificity_decision_1800.md`

## Read

This closes the first `c_proj` specificity gate negatively under the same
checkpoint, same schedule, same harness rule. The visible improvement in this
prefix still appears to be schedule/checkpoint-state behavior, not applied
LocoProp correction, for both `c_fc` and this `c_proj` test.
