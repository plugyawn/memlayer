# Prime Track 3 Simple LocoProp-M Run Snapshots

Saved on 2026-06-01 from the two active Prime 1xH100 target-3.28 runs.

## Runs

- `prime_a_seed200`: pod `8312077bfda9403fb5377b81c1e802e0`, host `216.81.248.32`
- `prime_b_seed300`: pod `b3ebfcf259094999b5a363fcd749e07d`, host `216.81.200.33`

Both used:

```bash
TRACK3_SOURCE=records/track_3_optimization/train_gpt_simple.py
TRACK3_TRAIN_STEPS=3350
TRACK3_NUM_TRIALS=1
TRACK3_TARGET_LOSS=3.28
TRACK3_MBS=16
TRACK3_DATA_CHUNKS=20
SCREEN_VAL_EVERY=125
NPROC_PER_NODE=1
TRACK3_LOCOM_ENABLED=1
TRACK3_LOCOM_LAYERS=all
TRACK3_LOCOM_STEPS=4
TRACK3_LOCOM_SAMPLE_TOKENS=1024
TRACK3_LOCOM_INNER_LR=0.1
TRACK3_LOCOM_TARGET_GAMMA=1.0
TRACK3_LOCOM_PROX=0.1
TRACK3_LOCOM_ALPHA=1.0
TRACK3_LOCOM_NORM_CAP=0.20
```

Seed offsets:

```bash
prime_a_seed200: TRACK3_SEED_OFFSET=200
prime_b_seed300: TRACK3_SEED_OFFSET=300
```

## Artifacts

- `final_track3_simple_locom_seed200/seed200_final_artifacts.tgz`
- `final_track3_simple_locom_seed300/seed300_final_artifacts.tgz`

Final artifacts copied immediately before pod cleanup. Each final archive contains
the generated train script, complete train log, status file, generation log, GPU text,
and launch wrapper log from the pod.

- `prime_a_seed200_snapshot_step2250ish_20260601.tgz`
- `prime_b_seed300_snapshot_step2250ish_20260601.tgz`

Each snapshot contains the exact generated train script, current train log, status file,
generation log, GPU text, and launch wrapper log from the pod.

- `prime_a_seed200_remote_repo_code_no_data_20260601.tgz` (large local-only snapshot)

Code-only copy of the remote repo from pod A, excluding `data/fineweb10B` and `logs`.
The remote checkout had no `.git` metadata. This tarball is intentionally kept as a
local recovery artifact rather than committed; the final generated scripts above are
the committed run-code snapshots.

- `prime_a_seed200_data_sha256_20260601.txt`

SHA-256 hashes for the 20 train chunks, validation chunk, and data helper files used by
the run. The 4.2GB dataset itself was not copied locally in this snapshot.

- `prime_a_seed200_runtime_manifest_20260601.txt`
- `prime_b_seed300_runtime_manifest_20260601.txt`

Runtime manifests with Python, PyTorch, CUDA package versions, pip freeze, and repo listing.

## Reproduction Shape

To reproduce from the generated script, restore the code tar, recreate or verify
`data/fineweb10B` against `prime_a_seed200_data_sha256_20260601.txt`, install the runtime
packages from the manifest, then run:

```bash
torchrun --standalone --nproc_per_node=1 <generated_train_script.py> 1
```

The two generated scripts have identical SHA-256 hashes; the seed offset is baked into
the generated code/log recipe for each pod.
