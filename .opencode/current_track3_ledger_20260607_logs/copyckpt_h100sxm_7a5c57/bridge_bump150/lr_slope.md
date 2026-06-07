# Track 3 LocoProp-M LR/Slope Join

## Step Values

| lane | category | step | val_loss | lr_frac | adam_frac | muon_frac |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| nohup | unknown | 2125 | 3.36215 | nan | nan | nan |
| nohup | unknown | 2250 | 3.35306 | nan | nan | nan |
| nohup | unknown | 2400 | 3.34638 | nan | nan | nan |
| track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400 | scheduler | 2125 | 3.36215 | nan | nan | nan |
| track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400 | scheduler | 2250 | 3.35306 | nan | nan | nan |
| track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400 | scheduler | 2400 | 3.34638 | nan | nan | nan |

## Window Slopes

| lane | category | window | drop | drop/step | rolling target/step | ratio | lr start | lr end | lr drop | status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| nohup | unknown | 2125->2250 | 0.00909 | 0.0000727 | 0.0000939 | 0.77x | nan | nan | nan | cold |
| nohup | unknown | 2250->2400 | 0.00668 | 0.0000445 | 0.0000974 | 0.46x | nan | nan | nan | cold |
| track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400 | scheduler | 2125->2250 | 0.00909 | 0.0000727 | 0.0000939 | 0.77x | nan | nan | nan | cold |
| track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400 | scheduler | 2250->2400 | 0.00668 | 0.0000445 | 0.0000974 | 0.46x | nan | nan | nan | cold |

## Read

- `nohup`: last healthy `none`, first cold `2125->2250`.
- `track3_suffix_bridge_bump150_2250_2650_from2125_seed3710_to2400`: last healthy `none`, first cold `2125->2250`.
