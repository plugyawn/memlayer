# Track 3 Post-2000 Suffix Manifest

| lane | enabled | local_opt | random | mode | norm_target | lr_min_eta | lr_bump_windows | intent |
| --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- |
| control | 0 | sgd | 0 | normal | 0.00 | 0.0000000000 | `` | no-correction cold-schedule control |
| floor111 | 0 | sgd | 0 | normal | 0.00 | 0.1111111111 | `` | LR floor at the step-2000 eta |
| floor111_norm002_k5 | 1 | sgd | 0 | normal | 0.02 | 0.1111111111 | `` | LR floor plus true-post c_fc K5 at 2% base-step norm |
| floor111_random002 | 1 | random | 1 | normal | 0.02 | 0.1111111111 | `` | LR floor plus same-shape random 2% correction |
| ramp111 | 0 | sgd | 0 | normal | 0.00 | 0.0000000000 | `2000:2250:2250:2400:1.7777777778` | smooth LR multiplier ramp targeting step-2000 eta near 2250 |

## LR Preview

| lane | 2000 | 2025 | 2050 | 2075 | 2100 | 2125 | 2200 | 2250 | 2325 | 2400 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 0.111111 | 0.105625 | 0.100278 | 0.095069 | 0.090000 | 0.085069 | 0.071111 | 0.062500 | 0.050625 | 0.040000 |
| floor111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 |
| floor111_norm002_k5 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 |
| floor111_random002 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 | 0.111111 |
| ramp111 | 0.111111 | 0.113840 | 0.115877 | 0.117252 | 0.118000 | 0.118152 | 0.115358 | 0.111111 | 0.070313 | 0.040000 |

Common invariants:

- `layers=all`
- `steps=5`
- `sample_tokens=1024`
- `target_space=post`
- `true_post_grad=True`
- `require_loss_decrease=True`
- `min_cos_desc=0.0`
- `inner_lr=0.0002`
- `prox=0.1`
- `alpha=1.0`
- `norm_to_base=False`
- `norm_cap=0.2`
- `target_loss=3.28`
- `seed_base=0`
- `seed_offset=3710`
- `cooldown_frac=1.0`
- `lr_schedule=power`
- `lr_power=2.0`
- `lr_schedule_steps=3000`
- `lr_switch_step=-1`
- `lr_after_switch=`
- `resume_load_optimizers=True`
