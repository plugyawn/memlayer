# Track 3 Rank/Subspace Diagnostic - 2026-06-08

Checkpoint-only SVD diagnostic run on the active Prime H100 pod.

Tool:

```text
tools/analyze_track3_rank_subspace.py
```

Inputs:

```text
red1600
good2000
cold2250
cold2400
cold2500
cold2600
```

Outputs:

```text
.opencode/diagnostics/track3_rankdiag_20260608/
```

## Main Read

The naive "our late weights are low rank" statement is too strong. The saved
model weights have moderate/high stable rank and the actual checkpoint deltas
are broad. The failure is better described as:

```text
Muon momentum / operand is very spectrally concentrated,
while checkpoint-to-checkpoint broad updates shrink rapidly in magnitude.
```

So the late failure is not fixed by a scalar Muon floor. That matches the live
`muon_floor006` result: it raised Muon LR after the floor bound, but validation
got worse.

## Weight Spectra

Median stable ranks stay almost unchanged from `1600` through `2600`.

```text
surface    red1600 sr   good2000 sr   cold2600 sr
mlp_fc     114.7        116.1         116.4
mlp_proj   128.6        129.8         128.5
attn_v     157.1        155.8         155.0
attn_o     139.8        138.3         139.1
```

Weight norms drift downward, but stable rank does not collapse.

```text
surface    red1600 fro  good2000 fro  cold2600 fro
mlp_fc     206.31       198.48        193.49
mlp_proj   104.85       100.82        98.25
attn_v     102.69       99.00         96.61
attn_o     96.18        92.56         90.27
```

## Momentum Spectra

Muon momentum is highly concentrated.

```text
surface    good2000 sr  cold2600 sr  cold2600 top32 energy
mlp_fc     4.4          3.9          0.474
mlp_proj   25.1         13.5         0.341
attn_v     5.1          4.9          0.667
attn_o     4.1          3.2          0.671
```

This is the "low-rank" object. Heating it late amplifies a concentrated
operand; it does not construct the missing late geometry.

## Delta Spectra

The actual parameter deltas remain broad, but their size falls fast.

Median `mlp_fc` delta Frobenius per step:

```text
1600 -> 2000: 0.0808
2000 -> 2250: 0.0526
2250 -> 2400: 0.0402
2400 -> 2500: 0.0321
2500 -> 2600: 0.0220
```

Median `attn_v` delta Frobenius per step:

```text
1600 -> 2000: 0.0359
2000 -> 2250: 0.0234
2250 -> 2400: 0.0179
2400 -> 2500: 0.0143
2500 -> 2600: 0.0098
```

The deltas have high stable rank:

```text
surface    1600->2000 sr   2500->2600 sr
mlp_fc     330.1           372.3
mlp_proj   326.7           367.2
attn_v     198.4           239.8
attn_o     201.1           236.9
```

So the problem is not that late updates are literally rank-1. It is that their
broad displacement is too small by the time the tail matters.

## MuP-Style Scaling Consequence

The current LocoProp scale is not MuP-clean:

```text
TRACK3_LOCOM_PROX = 0.1
TRACK3_LOCOM_NORM_CAP = 0.2
```

The cap is parameter/update-space, while feature learning should be controlled
by induced activation displacement:

```text
act_rms = rms(X @ delta_W.T)
```

The next scale should target:

```text
rms(X @ delta_W.T) / rms(X @ base_muon_delta.T)
```

or:

```text
rms(X @ delta_W.T) / rms(layer_activation)
```

not:

```text
||delta_W||_F / ||base_step||_F
```

Recommended first scale ladder:

```text
activation-relative-to-base: 0.5, 1.0, 1.5
activation-relative-to-layer: 0.02, 0.05, 0.10
```

Run it early, where the model still has LR budget and the 1600->2000 deltas are
large. Late activation scaling is a rescue probe only.
