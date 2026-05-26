# Feature-Gram Diagonal H100 Results

Fresh branch: `codex/wr-fresh-20260526`
Pod: `93b003de7290466abe00948cb9aa0330` (`oc-codex-fgdiag-h100-20260526`, 1x H100 80GB PCIe, $2.35/hr)

| variant | log | final train_time | final val_loss | notes |
| --- | --- | ---: | ---: | --- |
| upstream | `~/nanogpt-upstream/logs/upstream_full.log` | 937.278s | 3.2772 | clean upstream, same data/venv |
| upstream r2 | `~/nanogpt-upstream/logs/upstream_r2.log` | 931.476s | 3.2780 | repeat control; dominates MLP-only timing and loss |
| all surfaces inverse | `logs/fgdiag_atomic_full.log` | 945.816s | 3.2851 | slower and worse |
| all surfaces normalized sqrt | `logs/fgdiag_normsqrt_full.log` | 945.054s | 3.2774 | loss-neutral, too slow |
| MLP-only normalized sqrt r1 | `logs/fgdiag_normsqrt_mlp_full.log` | 933.083s | 3.2784 | faster, final loss worse |
| MLP-only normalized sqrt r2 | `logs/fgdiag_normsqrt_mlp_r2.log` | 932.659s | 3.2785 | repeated faster/worse |
| MLP-only normalized quarter r1 | `logs/fgdiag_normquarter_mlp_r1.log` | 933.232s | 3.2786 | strength reduction did not help final loss |
| MLP+O normalized sqrt r1 | `logs/fgdiag_normsqrt_mlp_o_r1.log` | 936.898s | 3.2798 | O recovered 750 loss but not final parity |

Current interpretation:

- Full diagonal Feature-Gram capture is not justified: all-surfaces normalized sqrt recovers loss but adds about 0.83% final train time.
- MLP-only capture is cheap, but the clean upstream repeat was faster and had better final loss than MLP-only; the original apparent speed win was baseline variance.
- Lowering MLP-only strength to power 0.25 did not improve final parity.
- MLP+O is not promotable: it gives back nearly all speed margin and ends worse than MLP-only.
- Feature-Gram diagonal approximation is not justified on the current path without a new algorithmic reason: all tested variants either lose quality, lose time, or are dominated by the upstream repeat.
