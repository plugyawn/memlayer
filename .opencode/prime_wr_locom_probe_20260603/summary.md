# Prime WR/LocoProp Probe, 2026-06-03

Platform: Prime Intellect B200 spot, pod `6d0a7c2ed83d4b138c8b4e9dc8ac6d0d`, terminated after probes.

## Objective

Test whether the LocoProp-M prefix advantage around `~2000-2200` can be converted into a quick Track 3 win by handing off to the current WR late optimizer stack.

## Runs

| run | read | validation points |
| --- | --- | --- |
| `wr_source_state_seed3710_step1600_b200` | WR source baseline and optimizer-state checkpoint source | `4.52095 @125`, `4.05268 @250`, `3.82397 @500`, `3.51853 @1600` |
| `wr_selfresume_state1600_seed3710_to1750_b200` | checkpoint/resume control; WR optimizer state reload works | `3.51760 @1625`, `3.48908 @1750` |
| `wr_splice_locom_model_wrstate1600_seed3710_b200` | LocoProp model state + mature WR optimizer/SOAP state | `3.50364 @1625`, `3.50240 @1750`, `3.47792 @1875`, `3.45222 @2000`, `3.42819 @2125` |
| `wr_record_locom_cotrain_k4_cap020_500_seed3710_b200` | WR stack + default additive LocoProp-M from step 0 | `4.51854 @125`, `4.05838 @250`, `~2153ms/step` |
| `wr_record_locom_cotrain_k5_lr1e5_gated_250_seed3710_b200` | WR stack + locally sane gated LocoProp-M from step 0 | `4.51990 @125`, `4.05212 @250`, `~2150ms/step` |

## Diagnosis

The suffix handoff problem is not only scalar LR. The current WR late stack has optimizer memory: Muon momentum, SOAP second moments, trust/floor history, and step-scheduled update geometry. A cold WR suffix reset was bad. A mature WR optimizer state from the WR trajectory was also bad when attached to the LocoProp model state. That means the mature state is not portable across the LocoProp trajectory.

The current WR+LocoProp co-train path is also not viable as implemented. Default `K=4, inner_lr=0.1` accepts local corrections even when the local solve worsens badly (`lossK >> loss0`) and sometimes points anti-descent. Gating and `inner_lr=1e-5` makes the local solve sane, but the update becomes tiny and only beats WR by `0.00056 @250` while more than doubling step time.

## Conclusion

This line does not currently produce a quick WR path:

- checkpoint suffixing loses the LocoProp advantage because optimizer state is incompatible;
- WR+LocoProp co-training is too slow and either unsafe (`inner_lr=0.1`) or too weak (`inner_lr=1e-5` gated);
- late LR scheduling alone cannot close the observed `2000->3000` descent gap.

The next productive direction would need either a compiled/fused LocoProp capture path so co-training is cheap enough to tune, or a much more direct update-map change in the existing WR substrate that does not require activation-hook LocoProp every step.
