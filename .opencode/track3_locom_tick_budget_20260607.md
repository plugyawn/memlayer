# Track 3 LocoProp-M Tick Budget

| log | step | k | eff/base med | cos med | aligned frac | alpha for 1% aligned | total norm then | alpha for 5% aligned | total norm then |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| active_k5 | 1600 | 5 | 0.0104 | 0.0045 | 0.000047 | 214.4x | 2.22x | 1072.2x | 11.11x |
| natural_k5 | 2000 | 5 | 0.0099 | 0.0090 | 0.000089 | 112.5x | 1.11x | 562.7x | 5.56x |
| natural_k5 | 2025 | 5 | 0.0091 | 0.0170 | 0.000155 | 64.5x | 0.59x | 322.7x | 2.94x |
| natural_k5 | 2050 | 5 | 0.0106 | 0.0070 | 0.000074 | 134.5x | 1.43x | 672.5x | 7.14x |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2500 | 5 | 0.0500 | 0.0095 | 0.000475 | 21.1x | 1.05x | 105.3x | 5.26x |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2525 | 5 | 0.0500 | 0.0095 | 0.000475 | 21.1x | 1.05x | 105.3x | 5.26x |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2550 | 5 | 0.0500 | 0.0080 | 0.000400 | 25.0x | 1.25x | 125.0x | 6.25x |
| track3_locom_tail2500_ungated_norm005_seed3710_to2600 | 2575 | 5 | 0.0500 | 0.0075 | 0.000375 | 26.7x | 1.33x | 133.3x | 6.67x |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2500 | 5 | 0.0500 | 0.0085 | 0.000425 | 23.5x | 1.18x | 117.7x | 5.88x |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2525 | 5 | 0.0500 | 0.0075 | 0.000375 | 26.7x | 1.33x | 133.3x | 6.67x |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2550 | 5 | 0.0500 | 0.0080 | 0.000400 | 25.0x | 1.25x | 125.0x | 6.25x |
| track3_locom_tail2500_ungated_softpolar_norm005_seed3710_to2600 | 2575 | 5 | 0.0500 | 0.0090 | 0.000450 | 22.2x | 1.11x | 111.1x | 5.56x |

Read: `total norm then` is the total LocoProp correction norm as a multiple of the base Muon step.
Large alpha with total norm near or above `1x` means scaling would create a major sideways perturbation.
