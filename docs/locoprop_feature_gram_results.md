# Diagonal Feature-Gram / LocoProp-S Probe Results

Branch: `codex/wr-fresh-20260526`

This branch is default-off. `run.sh` does not enable these probes; use
`LOCO_DIAG=1` plus the surface/mode env vars below.

The implementation currently tests a diagonal feature statistic, not the full
`FEATURE_GRAM = X.T @ X` optimizer from the design note. It is best understood
as feature-energy rescaling before the existing NorMuon/Polar-Express stack,
with a direct diagonal LocoProp-S mode kept as a diagnostic.

## Runtime Contract

Common env vars:

```bash
LOCO_DIAG=1
LOCO_DIAG_MODE=normuon
LOCO_DIAG_NORMUON_PRECOND=raw|normsqrt|normquarter
LOCO_DIAG_SURFACES=mlp_fc,mlp_proj|qk,v,o|v,o
LOCO_DIAG_MLP_LAYERS=all
LOCO_DIAG_ATTN_LAYERS=all
```

Current mode interpretation:

- `normuon`: precondition the stored gradient, then continue through momentum,
  Polar Express, NorMuon variance reduction, weight decay, and mantissa writes.
- `direct`: directly applies a diagonal LocoProp-S style update for MLP banks.
  This is a large optimizer swap and has not been competitive.
- `raw`: uses literal inverse diagonal scaling. This is too aggressive early.
- `normsqrt` and `normquarter`: mean-normalized inverse-power scaling before
  NorMuon. `normquarter` has been the least harmful of the MLP variants.

Data note: the 60-step and 200-step H100 screens used the same local cached data
setup for baseline and candidates. `fineweb_train_000002.bin` was duplicated
from the first shard after a Hugging Face download stall, so these screens are
valid for apples-to-apples early comparisons but not final record claims.

## Existing Full-Run Diagonal Screens

These runs are from `.opencode/fgdiag-results.md`.

| variant | final train_time | final val_loss | verdict |
| --- | ---: | ---: | --- |
| upstream | 937.278s | 3.2772 | clean control |
| upstream r2 | 931.476s | 3.2780 | repeat control |
| all surfaces inverse | 945.816s | 3.2851 | slower and worse |
| all surfaces normalized sqrt | 945.054s | 3.2774 | loss-neutral but too slow |
| MLP-only normalized sqrt r1 | 933.083s | 3.2784 | faster than one control, worse than repeat |
| MLP-only normalized sqrt r2 | 932.659s | 3.2785 | repeat confirms worse loss |
| MLP-only normalized quarter r1 | 933.232s | 3.2786 | lower strength did not fix loss |
| MLP+O normalized sqrt r1 | 936.898s | 3.2798 | not promotable |

## 1xH100 Early Screens

These were run on the same 1x H100 setup with 60 scheduled steps unless noted.
Raw evidence is committed under `.opencode/`.

| variant | log | final val_loss | final step_avg | delta vs baseline |
| --- | --- | ---: | ---: | --- |
| baseline | `.opencode/baseline_screen60.log` | 4.8502 | 672.76ms | reference |
| direct MLP, gamma 1 | `.opencode/locodiag_screen60.log` | 5.0387 | 683.12ms | worse loss, slower |
| direct MLP, gamma 4 | `.opencode/locodiag_gamma4_screen60.log` | 5.0265 | 684.05ms | worse loss, slower |
| MLP raw before NorMuon | `.opencode/locodiag_normuon_screen60.log` | 5.0237 | 686.04ms | worse loss, slower |
| MLP normsqrt before NorMuon | `.opencode/locodiag_normuon_normsqrt_screen60.log` | 4.9117 | 686.23ms | still worse |
| MLP normquarter before NorMuon | `.opencode/locodiag_normuon_normquarter_screen60.log` | 4.8794 | 686.33ms | closest MLP result |
| QKVO normquarter before NorMuon | `.opencode/locodiag_qkvo_normquarter_screen60.log` | 4.8637 | 683.92ms | slight loss recovery, slower |
| V/O normquarter before NorMuon | `.opencode/locodiag_vo_normquarter_screen60.log` | 4.8334 | 684.16ms | early loss win, slower |

The 200-step V/O check gives the first real positive signal, but the timing cost
is still too high:

| variant | log | final val_loss | final train_time | final step_avg |
| --- | --- | ---: | ---: | ---: |
| baseline 200 | `.opencode/baseline_screen200.log` | 3.8998 | 134.977s | 674.88ms |
| V/O normquarter 200 | `.opencode/locodiag_vo_normquarter_screen200.log` | 3.8937 | 136.669s | 683.35ms |

V/O normquarter improves 200-step validation by `0.0061` but costs `1.692s`
over 200 scheduled steps, about `+1.25%` wall time. That is interesting for
algorithmic follow-up, but not yet speedrun-positive.

## Current Interpretation

The MLP collection axes look correct, including `c_proj` row scaling against the
post-ReLU-squared feature. The failures are more likely optimizer-structural:

- `raw` inverse feature scaling before Polar Express corrupts early directions.
- changing `LOCO_DIAG_GAMMA` mostly cannot fix `normuon/raw`, because Polar
  Express removes the global matrix scale.
- `direct` removes the tuned NorMuon path for the MLP bank, so it is not a fair
  small perturbation.
- `mlp_proj` is likely noisier than `mlp_fc`, but the current guard prevents
  isolating those two surfaces.
- attention V/O is cheap enough to keep testing, but `sa_lambdas` mean direct
  Hessian scaling would need scalar-aware handling.

## Relevant Next Patch

Before more long runs, make the probe less aggressive and more debuggable:

1. Remove the guard that forces `mlp_fc` and `mlp_proj` to be enabled together.
2. Add relative-ridge, mean-normalized inverse-power scaling:

   ```python
   d = diag.float().clamp_min(0).mul(denom_scale)
   m = d.mean().clamp_min(1e-12)
   scale = (m / (d + ridge_rel * m)).pow(alpha)
   scale = scale / scale.mean().clamp_min(1e-12)
   scale = 1.0 + blend * (scale - 1.0)
   ```

3. Warm-start `blend` over the same rough horizon as NorMuon momentum warmup.
4. Add short-step diagnostics for feature diagonal spread and preconditioned
   gradient norm ratios.
5. Continue surface/layer ablations for `v,o` and then isolate `o` vs `v`.

## Promotion Bar

For this repo, a diagonal feature-Gram variant needs both:

- final validation no worse than baseline within about `0.002`, and
- at least a `2%` end-to-end train-time win on 1xH100 before spending 8xH100.

At roughly `675ms/step`, that means a candidate must recover more than the
current `~8ms/step` capture overhead through fewer required steps. The current
V/O result is promising on loss, but not enough on step time.
