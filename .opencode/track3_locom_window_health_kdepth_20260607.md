# Track 3 LocoProp-M Window Health

## Validation Values

| lane | category | 1600 | 1625 | 1650 | 1675 | 1700 | 1725 | 1750 | 1775 | 1800 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| track3_kdepth_k10-lr2e4_184734 | unknown | 3.48241 | 3.45134 | 3.43562 | 3.42615 | 3.41884 | 3.41289 | 3.40794 | 3.40360 | 3.39873 |
| track3_kdepth_k5-lr2e4_192742 | unknown | 3.48241 | 3.45135 | 3.43562 | 3.42613 | 3.41883 | 3.41289 | 3.40793 | 3.40361 | 3.39870 |
| track3_kdepth_k8-lr2e4_190744 | unknown | 3.48241 | 3.45135 | 3.43562 | 3.42613 | 3.41884 | 3.41287 | 3.40794 | 3.40362 | 3.39870 |

## Required Line

`track3_kdepth_k10-lr2e4_184734` target line: 3.48241 @ 1600 -> 3.28000 @ 3000

| step | required | actual | actual - required |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48241 | 3.48241 | +0.00000 |
| 1625 | 3.47880 | 3.45134 | -0.02746 |
| 1650 | 3.47518 | 3.43562 | -0.03956 |
| 1675 | 3.47157 | 3.42615 | -0.04542 |
| 1700 | 3.46795 | 3.41884 | -0.04911 |
| 1725 | 3.46434 | 3.41289 | -0.05145 |
| 1750 | 3.46072 | 3.40794 | -0.05278 |
| 1775 | 3.45711 | 3.40360 | -0.05351 |
| 1800 | 3.45349 | 3.39873 | -0.05476 |

`track3_kdepth_k5-lr2e4_192742` target line: 3.48241 @ 1600 -> 3.28000 @ 3000

| step | required | actual | actual - required |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48241 | 3.48241 | +0.00000 |
| 1625 | 3.47880 | 3.45135 | -0.02745 |
| 1650 | 3.47518 | 3.43562 | -0.03956 |
| 1675 | 3.47157 | 3.42613 | -0.04544 |
| 1700 | 3.46795 | 3.41883 | -0.04912 |
| 1725 | 3.46434 | 3.41289 | -0.05145 |
| 1750 | 3.46072 | 3.40793 | -0.05279 |
| 1775 | 3.45711 | 3.40361 | -0.05350 |
| 1800 | 3.45349 | 3.39870 | -0.05479 |

`track3_kdepth_k8-lr2e4_190744` target line: 3.48241 @ 1600 -> 3.28000 @ 3000

| step | required | actual | actual - required |
| ---: | ---: | ---: | ---: |
| 1600 | 3.48241 | 3.48241 | +0.00000 |
| 1625 | 3.47880 | 3.45135 | -0.02745 |
| 1650 | 3.47518 | 3.43562 | -0.03956 |
| 1675 | 3.47157 | 3.42613 | -0.04544 |
| 1700 | 3.46795 | 3.41884 | -0.04911 |
| 1725 | 3.46434 | 3.41287 | -0.05147 |
| 1750 | 3.46072 | 3.40794 | -0.05278 |
| 1775 | 3.45711 | 3.40362 | -0.05349 |
| 1800 | 3.45349 | 3.39870 | -0.05479 |

## Window Slopes

| lane | category | window | drop | drop/step | fixed-target ratio | rolling-target ratio | status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1600->1625 | 0.03107 | 0.0012428 | 8.60x | 8.60x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1625->1650 | 0.01572 | 0.0006288 | 4.35x | 5.05x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1650->1675 | 0.00947 | 0.0003788 | 2.62x | 3.29x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1675->1700 | 0.00731 | 0.0002924 | 2.02x | 2.65x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1700->1725 | 0.00595 | 0.0002380 | 1.65x | 2.23x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1725->1750 | 0.00495 | 0.0001980 | 1.37x | 1.90x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1750->1775 | 0.00434 | 0.0001736 | 1.20x | 1.70x | healthy |
| track3_kdepth_k10-lr2e4_184734 | unknown | 1775->1800 | 0.00487 | 0.0001948 | 1.35x | 1.93x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1600->1625 | 0.03106 | 0.0012424 | 8.59x | 8.59x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1625->1650 | 0.01573 | 0.0006292 | 4.35x | 5.05x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1650->1675 | 0.00949 | 0.0003796 | 2.63x | 3.29x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1675->1700 | 0.00730 | 0.0002920 | 2.02x | 2.65x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1700->1725 | 0.00594 | 0.0002376 | 1.64x | 2.22x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1725->1750 | 0.00496 | 0.0001984 | 1.37x | 1.90x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1750->1775 | 0.00432 | 0.0001728 | 1.20x | 1.69x | healthy |
| track3_kdepth_k5-lr2e4_192742 | unknown | 1775->1800 | 0.00491 | 0.0001964 | 1.36x | 1.95x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1600->1625 | 0.03106 | 0.0012424 | 8.59x | 8.59x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1625->1650 | 0.01573 | 0.0006292 | 4.35x | 5.05x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1650->1675 | 0.00949 | 0.0003796 | 2.63x | 3.29x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1675->1700 | 0.00729 | 0.0002916 | 2.02x | 2.64x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1700->1725 | 0.00597 | 0.0002388 | 1.65x | 2.24x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1725->1750 | 0.00493 | 0.0001972 | 1.36x | 1.89x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1750->1775 | 0.00432 | 0.0001728 | 1.20x | 1.69x | healthy |
| track3_kdepth_k8-lr2e4_190744 | unknown | 1775->1800 | 0.00492 | 0.0001968 | 1.36x | 1.95x | healthy |

## Read

- `track3_kdepth_k10-lr2e4_184734`: last healthy window `1775->1800`; first cold window `none`.
- `track3_kdepth_k5-lr2e4_192742`: last healthy window `1775->1800`; first cold window `none`.
- `track3_kdepth_k8-lr2e4_190744`: last healthy window `1775->1800`; first cold window `none`.
