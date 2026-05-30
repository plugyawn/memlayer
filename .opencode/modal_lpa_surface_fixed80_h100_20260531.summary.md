| surface | case | final_step | val_loss | train_time_s | step_avg_ms |
| --- | --- | ---: | ---: | ---: | ---: |
| v | paired_active | 80 | 4.5250 | 36.330 | 454.12 |
| v | paired_noop | 80 | 4.5250 | 36.194 | 452.43 |
| v | paired_noop2 | 40 | 5.6055 | 12.516 | 312.90 |
| mlp_fc | paired_active | 80 | 4.5251 | 36.132 | 451.65 |
| mlp_fc | paired_noop | 80 | 4.5235 | 36.129 | 451.61 |
| mlp_fc | paired_noop2 | 80 | 4.5224 | 36.151 | 451.89 |
| o | paired_active | 80 | 4.5239 | 36.195 | 452.44 |
| o | paired_noop | 80 | 4.5189 | 36.074 | 450.93 |
| o | paired_noop2 | 80 | 4.5209 | 36.133 | 451.67 |

| surface | active | noop1 | noop2 | delta_vs_noop_mean | beats_both | read |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| v | 4.525 | 4.525 | 5.6055 |  | incomplete | incomplete/interrupted |
| mlp_fc | 4.5251 | 4.5235 | 4.5224 | +0.0022 | no | worse/inconclusive |
| o | 4.5239 | 4.5189 | 4.5209 | +0.0040 | no | worse/inconclusive |
| qk |  |  |  |  | incomplete | incomplete/interrupted |
