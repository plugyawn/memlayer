# Newton-Muon Cycle Log - 2026-05-27

## Cycle 1 GPU Window

Time accounting:

- GPU window started: about `2026-05-27 17:00 IST`.
- Warm-metric H100 app: `ap-sSL50qhWTRJ3JKcQBp5FJ3`, `17:00-17:24 IST`, `1402.985s`.
- Overpreconditioning H100 app: `ap-9WOCEPdPIu5SZKslqZsOtb`, `17:28-17:49 IST`, `1217.204s`.
- GPU window ended: about `2026-05-27 17:49 IST`.
- Required meditation/audit window: `17:49-18:49 IST`.
- Next H100 launch allowed: `2026-05-27 18:49 IST`, unless the user overrides.

All NanoGPT Modal apps from this cycle were stopped after completion.

## Warm-Metric Result

The decoupled collect/apply control worked mechanically:

```text
collect C early
apply preconditioner later
```

But it did not produce a durable 120-step win:

| case | step 80 | step 120 |
| --- | --- | --- |
| baseline | `4.6326` | `4.1832` |
| V 0-1 collect 0-48 apply 48-112 polar4 | `4.6256` | `4.1829` |
| V 0-1 collect 0-64 apply 48-112 polar4 | `4.6282` | `4.1846` |
| O collect 0-64 apply 48-112 polar4 | `4.6339` | `4.1861` |
| V+O 0-1 collect 0-64 apply 48-112 polar4 | `4.6248` | `4.1847` |

Read: warm collection moves early loss, but by itself is not persistent enough.

## Overpreconditioning Result

The overpreconditioning ladder produced the strongest same-suite result:

| case | step 80 | step 120 |
| --- | --- | --- |
| baseline | `4.6244` | `4.1869` |
| warm V no-op polar4 | `4.6108` | `4.1798` |
| warm V active polar5 | `4.6183` | `4.1821` |
| warm V active polar4 | `4.6182` | `4.1763` |
| warm V active polar4 skip varred | `4.6192` | `4.1784` |

Read:

- `LOCO_FULL_POLAR_ITERS=4` matters.
- Active V polar4 beat baseline and the no-op control in this suite.
- `LOCO_FULL_SKIP_VARRED=1` was worse, so keep NorMuon variance reduction.
- Active polar5 was worse than no-op.

Important caveat:

The no-op control in this logged overprecond run used all V layers because it
used `tools/run_newtonv_timing_triplet_gate.sh`, whose default
`LOCO_DIAG_ATTN_LAYERS` is `all`. The active V cases used
`tools/run_newtonv_raw_v01_gate.sh`, whose default is `0-1`.

This has been fixed for future suites by setting `LOCO_DIAG_ATTN_LAYERS=0-1`
on matched no-op controls.

## No-Op Mechanism

`LOCO_FULL_NOOP=1` is not pure baseline plus overhead.

During the apply window, it sets full blend to zero but still activates the
full after-momentum optimizer path:

```text
raw grad
-> nesterov_momentum_operand_inplace
-> feature preconditioner helper with blend=0
-> polar_express_from_operand using LOCO_FULL_POLAR_ITERS
-> NorMuon variance reduction
```

So no-op is a real optimizer schedule/control:

```text
baseline path: fused polar_express with 5 coefficients
full no-op path: explicit momentum operand + polar_express_from_operand with LOCO_FULL_POLAR_ITERS
```

This makes no-op a useful candidate in its own right, not just a cost control.

## Next H100 Gate

Use the prepared `overpromote` suite:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"overpromote","NEWTONV_SUITE_LABEL":"modal_overpromote_h100_20260527","PROMOTE_STEPS":"200","PROMOTE_VAL_EVERY":"50"}' \
SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 \
tools/run_modal_newtonv_raw_gate.sh
```

It runs:

```text
baseline
V 0-1 no-op polar4
V 0-1 no-op polar5
all-V no-op polar4
V 0-1 active polar5
V 0-1 active polar4
```

Promotion rule:

```text
Promote only if V 0-1 active polar4 beats baseline, matched V0-1 no-op polar4,
and the matched active/no-op polar5 controls by at least 0.002 at 200 steps.
```

If matched no-op, active polar5, or all-V no-op beats active polar4, demote or
narrow Newton-specific right preconditioning and study the polar/full-path
schedule as its own optimizer lever.
