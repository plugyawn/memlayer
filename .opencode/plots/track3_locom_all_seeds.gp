set terminal pngcairo size 2200,1300 enhanced font "Arial,18"
set output ".opencode/plots/track3_locom_all_seeds.png"
set multiplot layout 2,1 title "All parsed Track 3 LocoProp-M seed curves" font ",22"
set grid
set key outside right top font ",10"
set xlabel "optimizer step"
set ylabel "validation loss"
set xrange [0:3350]
set yrange [3.25:4.72]
set arrow 1 from graph 0, first 3.28 to graph 1, first 3.28 nohead dt 2 lc rgb "#444444"
plot ".opencode/plots/track3_locom_dat/Prime3350_mean.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "black" pt 7 ps 0.35 title "Prime3350 mean",\
  ".opencode/plots/track3_locom_dat/Prime3350_seed200.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#999999" pt 7 ps 0.35 title "Prime3350 seed200",\
  ".opencode/plots/track3_locom_dat/Prime3350_seed300.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#bbbbbb" pt 7 ps 0.35 title "Prime3350 seed300",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1000.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1000",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1100.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1100",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1200.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1200",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1300.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1300",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1400.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1400",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1500.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1500",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed900.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed900",\
  ".opencode/plots/track3_locom_dat/Modal3100_seed400.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#2ca02c" pt 7 ps 0.35 title "Modal3100 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed400.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#d62728" pt 7 ps 0.35 title "Modal3250 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed500.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#ff7f0e" pt 7 ps 0.35 title "Modal3250 seed500",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1600.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#1f77b4" pt 7 ps 0.35 title "Modal3250 seed1600",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1700.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#9467bd" pt 7 ps 0.35 title "Modal3250 seed1700"
set xlabel "optimizer step"
set ylabel "delta vs Prime mean"
set xrange [0:3350]
set yrange [-0.055:0.025]
set arrow 1 from graph 0, first 0 to graph 1, first 0 nohead dt 2 lc rgb "#444444"
plot ".opencode/plots/track3_locom_dat/Prime3350_seed200_delta.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#999999" pt 7 ps 0.35 title "Prime3350 seed200",\
  ".opencode/plots/track3_locom_dat/Prime3350_seed300_delta.dat" using 1:2 with linespoints lw 1.5 dt 1 lc rgb "#bbbbbb" pt 7 ps 0.35 title "Prime3350 seed300",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1000_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1000",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1100_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1100",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1200_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1200",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1300_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1300",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1400_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1400",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed1500_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed1500",\
  ".opencode/plots/track3_locom_dat/Modal3000_seed900_delta.dat" using 1:2 with linespoints lw 1 dt 2 lc rgb "#cccccc" pt 7 ps 0.35 title "Modal3000 seed900",\
  ".opencode/plots/track3_locom_dat/Modal3100_seed400_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#2ca02c" pt 7 ps 0.35 title "Modal3100 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed400_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#d62728" pt 7 ps 0.35 title "Modal3250 seed400",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed500_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#ff7f0e" pt 7 ps 0.35 title "Modal3250 seed500",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1600_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#1f77b4" pt 7 ps 0.35 title "Modal3250 seed1600",\
  ".opencode/plots/track3_locom_dat/Modal3250_seed1700_delta.dat" using 1:2 with linespoints lw 3 dt 1 lc rgb "#9467bd" pt 7 ps 0.35 title "Modal3250 seed1700"
unset multiplot
