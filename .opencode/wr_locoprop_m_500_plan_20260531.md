# WR LocoProp-M 500-Step Smoke Plan

## Scope

Prepared a generated-script wrapper for the current WR-style `train_gpt.py` path. This does not launch Modal or touch any running apps.

The implementation is intentionally narrow:

- surface: MLP `c_fc` only, stored in `model.mlp_bank[layer, 0]`
- capture: sampled `mlp_in`, post-ReLU-squared activation, and `dpre` from the same fused MLP autograd path
- local objective: matching target `post - gamma * dpre`
- local solve: `K` sampled LocoProp-M matching steps
- application: state-decoupled post-NorMuon displacement on the owner rank's `mlp_bank` shard, before all-gather
- safety: norm cap relative to the baseline NorMuon step, optimizer momentum/variance state untouched
- constraint: no extra full-model forward/backward passes

## Key Integration Points

`train_gpt.py` uses banked fused MLPs:

- `mlp_bank[:, 0]` is `c_fc`, shape `[3072, 768]`
- `mlp_bank[:, 1]` is `c_proj`, shape `[3072, 768]`
- forward path unbinds `mlp_bank.flatten(0, 1)` and calls `ReLUSqrdMLP(mlp_in, c_fc, c_proj)`

The generated script imports `linear_relu_square` from `triton_kernels.py` and defines `FusedLinearReLUSquareLocoMFunction`, mirroring the original fused autograd function while sampling:

- `x`: the normalized MLP input
- `post`: `relu(x @ c_fc.T)^2`
- `dpre`: the fused backward preactivation gradient

The generated script inserts `prepare_wr_locoprop_m(...)` before `optimizer.step(...)`, then applies the correction inside `_normuon_update(...)` after the normal NorMuon update has produced `p_slice`, preserving sharded all-gather semantics.

## Dry Run

Local syntax/dry-run only:

```bash
WR_LOCOM_DRY_RUN=1 \
SCREEN_STEPS=500 \
NPROC_PER_NODE=8 \
bash tools/run_wr_locoprop_m_500.sh
```

This writes and py-compiles:

```text
/tmp/train_gpt_wr_locoprop_m_500.py
```

## Suggested 8xH100 Launch Env

Do not run this from a worker that did not start the Modal app. For the owning worker/operator:

```bash
NANOGPT_MODAL_GPU=H100:8 \
MODAL_GPU=H100:8 \
MODAL_RUN_NAME=wr-locom-m-k4-500-h100x8-r1 \
MODAL_RUNNER=tools/run_wr_locoprop_m_500.sh \
SCREEN_STEPS=500 \
SCREEN_VAL_EVERY=125 \
NPROC_PER_NODE=8 \
MODAL_DATA_CHUNKS=20 \
MODAL_EXTRA_ENV_JSON='{
  "WR_LOCOM_ENABLED": "1",
  "WR_LOCOM_LAYERS": "all",
  "WR_LOCOM_STEPS": "4",
  "WR_LOCOM_SAMPLE_TOKENS": "2048",
  "WR_LOCOM_INNER_LR": "0.1",
  "WR_LOCOM_TARGET_GAMMA": "1.0",
  "WR_LOCOM_PROX": "0.1",
  "WR_LOCOM_ALPHA": "1.0",
  "WR_LOCOM_NORM_CAP": "0.20",
  "WR_LOCOM_LOG_STEPS": "0,1,2,10,50,125,250,500"
}' \
bash tools/run_modal_newtonv_raw_gate.sh
```

For a second replicate, use a different `MODAL_RUN_NAME`. If an explicit seed is needed, add `TRAIN_RUN_SEED`.

## Notes And Risks

- The wrapper skips `torch.compile` by default when `WR_LOCOM_ENABLED=1`, because Python-side activation sampling and custom autograd side effects are unlikely to survive `fullgraph=True`. Set `WR_LOCOM_COMPILE=1` only for a deliberate compile experiment.
- The local correction is owner-local after an all-gather of sampled activation rows. This matches the active Track 3 LocoProp-M wrapper's semantics more closely than purely local samples.
- The correction uses the existing mantissa-aware `_cautious_wd_and_update_inplace` with zero weight decay and a negated displacement, so the direct parameter displacement still routes through the WR bank precision machinery.
- Default `WR_LOCOM_SAMPLE_TOKENS=2048` means each rank samples about 256 rows on 8xH100, then owner ranks gather to 2048 rows for the local solve.
- This is a smoke implementation, not speed-optimized. The local MLP matching solve is dense FP32 sampled math and is expected to be slow.
