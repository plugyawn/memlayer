| case | final_step | final_val_loss | final_train_time_s | final_step_avg_ms | refresh_step_ms_avg | nonrefresh_step_ms_avg | peak_alloc_mib |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mbc_baseline | 200 | 3.8854 | 130.53 | 652.65 |  | 652.17 | 37327 |
| mbc_schedule_only_before_r020_blend005 | 200 | 3.8876 | 120.81 | 604.03 |  | 603.55 | 37327 |
| mbc_noop_before_r020_blend005 | 200 | 3.8830 | 118.99 | 594.96 | 324.25 | 601.41 | 37440 |
| mbc_inverse_before_r020_blend005 | 200 | 3.8832 | 117.60 | 588.02 | 322.27 | 594.34 | 37440 |

Note: the first baseline attempt was preempted at step 67 and is omitted from
the table above. The completed restarted baseline is the 200-step row.
