# Clean LocoProp-M on Base Muon

This result directory starts from the pre-SinkSOAP Track 3 base Muon script and
adds one isolated LocoProp-M correction path.

The base optimizer is unchanged: AdamW handles embeddings, output projection,
and scalar parameters; Muon handles block matrices. LocoProp-M is implemented as
an additive local correction on MLP `fc` weights only. It does not feed the local
solve into Muon momentum or any persistent optimizer state.

Default run:

```bash
torchrun --standalone --nproc_per_node=1 \
  records/track_3_optimization/results/20260608_locom_clean/train_gpt_simple_locom_clean.py
```

Main controls:

```bash
TRACK3_LOCOM_ENABLED=1
TRACK3_LOCOM_MODE=matching
TRACK3_LOCOM_LAYERS=all
TRACK3_LOCOM_AUX_SEQS=1
TRACK3_LOCOM_SAMPLE_TOKENS=1024
TRACK3_LOCOM_STEPS=5
TRACK3_LOCOM_INNER_LR=0.10
TRACK3_LOCOM_PROX=0.10
TRACK3_LOCOM_TARGET_GAMMA=1.0
TRACK3_LOCOM_ALPHA=1.0
TRACK3_LOCOM_NORM_CAP=0.20
```

Implementation notes:

- The auxiliary capture path runs a small uncompiled forward and computes
  gradients only with respect to selected MLP pre-activations via
  `torch.autograd.grad`, so main parameter gradients remain the base Muon
  gradients.
- The local solver is batched across rank-owned MLP `fc` layers and uses
  deterministic stride sampling, avoiding per-step RNG changes.
- `matching` mode uses the LocoProp-M matching-loss gradient shape for the
  `relu^2` MLP activation: the local error is `relu(Wx+b)^2 - target`, but the
  local weight gradient is `error.T @ x` rather than ordinary backprop through
  `relu^2`.
- The correction `W_local - W0` is applied after the Muon update and is capped
  relative to that parameter's Muon step norm.
- Set `TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1` or
  `TRACK3_LOCOM_MIN_COS_DESC=<value>` for stricter screening.
