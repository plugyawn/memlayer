set terminal pngcairo size 2000,900 enhanced font "Arial,18"
set output ".opencode/plots/track3_locom_delta_vs_prime_mean.png"
set title "Delta vs Prime3350 two-seed mean (negative is better)"
set grid
set key outside right top font ",12"
set xlabel "optimizer step"
set ylabel "loss - Prime3350 mean"
set xrange [0:3350]
set yrange [-0.035:0.018]
set arrow from graph 0, first 0 to graph 1, first 0 nohead dt 2 lc rgb "#444444"
plot ".opencode/plots/track3_locom_dat/Prime3350_seed200_delta.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#999999" pt 7 ps 0.35 title "Prime3350 seed200",\
  ".opencode/plots/track3_locom_dat/Prime3350_seed300_delta.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#bbbbbb" pt 7 ps 0.35 title "Prime3350 seed300",\
  ".opencode/plots/track3_locom_dat/Modal3100_seed400_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#2ca02c" pt 7 ps 0.35 title "Modal3100 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed400_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#d62728" pt 7 ps 0.35 title "Modal3250 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed500_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#ff7f0e" pt 7 ps 0.35 title "Modal3250 seed500",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1600_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#1f77b4" pt 7 ps 0.35 title "Modal3250 seed1600",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1700_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#9467bd" pt 7 ps 0.35 title "Modal3250 seed1700"
