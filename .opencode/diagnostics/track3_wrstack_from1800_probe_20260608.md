# Track 3 WR-Stack From-1800 Probe

Date: 2026-06-08

Purpose: test whether a LocoProp/coldp2 prefix that reaches `3.39871 @1800`
benefits from switching to the current-record WR optimizer machinery with the
full 324-float-tensor optimizer2 state shape.

## Hardware

- Prime pod: `1f152db2580b48e7abac0db02b33f50c`
- GPU: `NVIDIA H100 80GB HBM3`, SXM5, datacrunch, `$3.25/hr`
- Status: terminated after logs/state diagnostics were pulled.

## Artifacts

- Logs: `.opencode/current_track3_ledger_20260608_logs/wrstack_from1800_1f152db2580b48e7abac0db02b33f50c/remote_logs/`
- Recreated local step-1800 checkpoint: `/Users/progyan/speedrun/tmp/prime_wrstack_from1800_checkpoints/track3_k5_coldp2_seed3710_to1800_seed3710_step1800.pt`
- Launcher: `tools/launch_prime_track3_wrstack_from1800_probe.sh`

## Curves

Common source:

| Step | K5/coldp2 regen |
| ---: | ---: |
| 1600 | 3.48241 |
| 1700 | 3.41883 |
| 1775 | 3.40359 |
| 1800 | 3.39871 |

Same 1800 state, two continuations:

| Step | Simple coldp2 | WR stack |
| ---: | ---: | ---: |
| 1875 | 3.38816 | 3.47212 |
| 2000 | 3.37335 | 3.45648 |
| 2125 | 3.36214 | 3.43429 |
| 2250 | 3.35305 | 3.41066 |
| 2375 | 3.34628 | 3.38799 |
| 2500 | 3.34113 | 3.36644 |

## State Counts

From `state_counts.txt`:

| Checkpoint | opt2 float tensors | opt2 float norm | opt2 keys |
| --- | ---: | ---: | --- |
| step1800 source | 144 | `2.389e3` | `momentum`, `last_update_norm` |
| simple step2500 | 144 | `2.968e3` | `momentum`, `last_update_norm` |
| WR step2500 | 324 | `6.446e7` | `momentum`, `second_moment`, SOAP state |

## Conclusion

The full WR machinery did allocate the expected 324-float-tensor optimizer2
state, but switching it on at step 1800 caused a large handoff shock and never
caught the simple continuation by step 2500.

This falsifies the narrow hypothesis that the late failure is fixed by merely
restarting from the LocoProp/coldp2 1800 weights with the WR optimizer2
machinery. The missing thing is not just the existence of the WR state schema;
it is the trajectory/state accumulated earlier under that optimizer.
