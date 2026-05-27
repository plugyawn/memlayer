# Modal Speedrun Notes

## Auth Status

The local environment currently has `MODAL_KEY`, and its shape matches a Modal
token id. Modal's documented auth requires both `MODAL_TOKEN_ID` and
`MODAL_TOKEN_SECRET`, or an equivalent `~/.modal.toml` written by
`modal token set`.

The utility `tools/modal_billing_check.sh` maps `MODAL_KEY` to
`MODAL_TOKEN_ID` for compatibility, then runs:

```bash
modal token info
modal billing report --for "this month" --json
```

This checks whether the token pair is complete and reports month-to-date spend.
Modal's public CLI/API exposes billing reports, not a direct remaining-credit
wallet field; remaining credits still need the dashboard unless Modal exposes a
new endpoint.

## H100 Probe

Once `MODAL_TOKEN_SECRET` is available locally:

```bash
python -m pip install modal
set -a; . /Users/progyan/speedrun/env.local; set +a
MODAL_TOKEN_ID="${MODAL_TOKEN_ID:-$MODAL_KEY}" modal run tools/modal_h100_probe.py
```

Expected proof of spawn:

- `nvidia-smi` reports an H100-class GPU.
- `MODAL_CLOUD_PROVIDER` and `MODAL_REGION` are populated.
- `nvcc` is available from the CUDA devel image.

## Fit For NanoGPT Speedrun Work

Modal is likely better than Prime for short, queued, reproducible screens after
the image and volumes are warm:

- pay per second instead of keeping a pod alive during setup and decisions;
- no SSH lifecycle cleanup;
- one-command `H100` or `H100:8` requests;
- H100 requests are SXM-class and may auto-upgrade to H200 at H100 pricing.

It is worse for exploratory remote debugging until the image/cache path is
stable:

- H100 list price is about `$0.001097/sec`, or `$3.95/hr`, before CPU/RAM;
- recent Prime H100 PCIe screens were `$2.35/hr`;
- initial image builds and dataset/cache population can dominate tiny screens;
- Modal notes that requests above two GPUs can have longer waits.

## Run Optimization Strategy

Use Modal for narrow candidates, not broad fishing:

1. Build one immutable CUDA image with Python, `torch==2.10`, `kernels==0.11.7`,
   repo requirements, and the CUDA devel toolchain.
2. Store FineWeb shards, Hugging Face kernel artifacts, and TorchInductor cache
   in Modal Volumes.
3. Generate `train_gpt_screen.py` locally before the Modal call so each run uses
   the same screen script and env toggles as Prime.
4. Run 1xH100 screens through a single Modal function with explicit run tags:
   branch, commit, surface, filter, layer set, steps, and seed/data shard.
5. Keep app `scaledown_window` short for one-off screens; only keep warm
   containers while launching a same-family ablation sequence.
6. Promote to `gpu="H100:8"` only after the 1xH100 candidate clears both loss
   and wall-clock gates. Modal supports up to eight H100s in one container, but
   the queue cost is only justified after the candidate is already clean.

