# Modal Speedrun Notes

## Auth And Billing Status

The local environment now has `MODAL_KEY_ID` and `MODAL_SECRET`. The local
helpers map those to Modal's standard `MODAL_TOKEN_ID` and
`MODAL_TOKEN_SECRET`, so the CLI authenticates without writing a persistent
`~/.modal.toml`.

The utility `tools/modal_billing_check.sh` redacts token output, then reports
month-to-date spend:

```bash
set -a; . /Users/progyan/speedrun/env.local; set +a
tools/modal_billing_check.sh
```

Current check on 2026-05-27:

```text
workspace: nipsdwip
month_to_date_pre_credit_usd: 1394.67
top spend: vla-adapter-libero-eval 1033.92, vla-adapter-calvin-baseline 360.74
starter_monthly_free_credit_remaining: 0.00
team_monthly_free_credit_remaining: 0.00
```

Modal's public billing CLI/API reports pre-credit/pre-reservation spend. Exact
remaining private grants or wallet balance still require the Usage & Billing
dashboard. The normal monthly free credit is exhausted either way.

## H100 Probe

The H100 probe works with the updated env mapping via:

```bash
python -m pip install modal
set -a; . /Users/progyan/speedrun/env.local; set +a
export MODAL_TOKEN_ID="${MODAL_TOKEN_ID:-${MODAL_KEY_ID:-$MODAL_KEY}}"
export MODAL_TOKEN_SECRET="${MODAL_TOKEN_SECRET:-$MODAL_SECRET}"
modal run tools/modal_h100_probe.py
```

Expected proof of spawn:

- `nvidia-smi` reports an H100-class GPU.
- `MODAL_CLOUD_PROVIDER` and `MODAL_REGION` are populated.
- `nvcc` is available from the CUDA devel image.

Live probe on 2026-05-27 succeeded with the lightweight base image:

```text
gpu_spec: H100
region: CANADA-2
gpu: NVIDIA H100 80GB HBM3, 81559 MiB
driver: 580.95.05
app state after probe: stopped
```

## Fit For NanoGPT Speedrun Work

Modal is likely better than Prime for short, queued, reproducible screens after
the image and volumes are warm:

- pay per second instead of keeping a pod alive during setup and decisions;
- no SSH lifecycle cleanup;
- one-command `H100` or `H100:8` requests;
- H100 requests are SXM-class and may auto-upgrade to H200 at H100 pricing.

It is worse for exploratory remote debugging until the image/cache path is
stable:

- H100 list price is `$0.001097/sec`, or `$3.95/hr`, before CPU/RAM;
- recent Prime H100 PCIe screens were `$2.35/hr`;
- initial image builds and dataset/cache population can dominate tiny screens;
- Modal notes that requests above two GPUs can have longer waits.

Modal's published GPU list does not include GH200. Under the current
`H100/GH200 only` constraint, the Modal runner defaults to `H100!`, Modal's
strict-H100 request string, so training metrics are not silently mixed with an
automatic H200 upgrade. `GH200` is accepted by the wrapper only to make the
constraint explicit, but Modal may reject it until it becomes a supported GPU
string.

## Run Optimization Strategy

Use Modal for narrow candidates, not broad fishing:

1. Build one immutable CUDA image with Python, `torch==2.10`, `kernels==0.11.7`,
   repo requirements, and the CUDA devel toolchain.
2. Store FineWeb shards, Hugging Face kernel artifacts, Triton cache, and
   TorchInductor cache in Modal Volumes.
3. Prepare data with a CPU function before requesting an H100, so GPU time is
   not burned on dataset downloads.
4. Generate `train_gpt_screen.py` inside the container using the same repo tool
   and env toggles as Prime.
5. Run 1xH100 screens through a single Modal function with explicit run tags:
   branch, commit, surface, filter, layer set, steps, and data chunk count.
6. Keep app `scaledown_window=60` for immediate same-family ablations; otherwise
   let the container die quickly.
7. Promote to `gpu="H100:8"` only after the 1xH100 candidate clears both loss
   and wall-clock gates.

## Prepared Cached Runner

`tools/modal_nanogpt_runner.py` is the efficient Modal path. It uses:

- immutable CUDA/Python image with `torch==2.10` and `kernels==0.11.7`;
- `nanogpt-speedrun-fineweb10b` volume mounted at `data/fineweb10B`;
- `nanogpt-speedrun-cache` volume mounted at `/root/.cache`;
- persistent `HF_HOME`, `TRITON_CACHE_DIR`, and `TORCHINDUCTOR_CACHE_DIR`;
- separate CPU data preparation from GPU training;
- returned JSON with Modal wall time and parsed training metric.

Cheap CPU/data warmup, no GPU:

```bash
set -a; . /Users/progyan/speedrun/env.local; set +a
modal run tools/modal_nanogpt_runner.py::prepare --data-chunks 2
```

First H100 screen:

```bash
set -a; . /Users/progyan/speedrun/env.local; set +a
MODAL_GPU='H100!' SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 \
  tools/run_modal_newtonv_raw_gate.sh
```

This keeps setup/download/build time outside the training metric, while still
reporting Modal wall time separately in the returned JSON.
