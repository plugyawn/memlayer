# Paperfilter Diagnostics

Raw log: `.opencode/modal_newtonv_paperfilter_h100_20260527.log`

## Operand Ratio

`loco_diag_grad_ratio` is the post-helper operand/update norm ratio reported by
the training script.

| case | step | n | mean | min | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| no-op polar4 | 50 | 2 | 1.0000 | 1.0000 | 1.0000 |
| no-op polar4 | 100 | 2 | 1.0000 | 1.0000 | 1.0000 |
| inverse V 0-1 | 50 | 2 | 0.9966 | 0.9962 | 0.9970 |
| inverse V 0-1 | 100 | 2 | 0.9417 | 0.9415 | 0.9419 |
| finite all-V | 50 | 10 | 0.9965 | 0.9964 | 0.9966 |
| finite all-V | 100 | 10 | 0.9449 | 0.9421 | 0.9466 |
| power0.5 all-V | 50 | 10 | 0.9961 | 0.9960 | 0.9961 |
| power0.5 all-V | 100 | 10 | 0.9378 | 0.9351 | 0.9401 |

## Timing Read

The step-80 validation boundary consistently inserted a large one-off step
after validation. Use final `step_avg` for same-suite comparisons, but do not
over-interpret the refresh/non-refresh split in this particular run.

| case | refresh avg | non-refresh avg | note |
| --- | ---: | ---: | --- |
| no-op polar4 | 386.56ms | 586.43ms | no active helper effect |
| inverse V 0-1 | 379.37ms | 577.95ms | active helper, n=2 |
| finite all-V | 490.38ms | 577.41ms | mislabeled `v01`, actually all V |
| power0.5 all-V | 489.61ms | 577.88ms | mislabeled `v01`, actually all V |

## Conclusion

The active filters moved the operand by roughly `5-6%` by step 100, but did not
beat the matched no-op/polar4 control at step 120. The finite and power cases
must be rerun layer-correct before drawing a V `0-1` conclusion.
