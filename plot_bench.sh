#!/bin/bash
OUT='graph.svg'
MY='my.txt'
GREP='grep.txt'

#python3 ./bench_my.py >$MY
#python3 ./bench_grep.py >$GREP

awk '{getline f1 < "grep.txt"; $2 = $2 OFS f1; print}' my_good.txt > scatter.txt #FIXME:file names and sizes

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "$OUT"

    set multiplot

    set ylabel "Time (s)" font ",18"
    set xlabel "Input length" font ",18"
    set logscale
    set grid

    plot "$MY" title "RsA implementation" with lines linestyle 1, "$GREP" title "grep implementation" with lines linestyle 2
EOFMarker

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "scatter.svg" #FIXME:    

    set multiplot

    set ylabel "grep time (s)" font ",18"
    set xlabel "RsA time (s)" font ",18"
    set xrange [:300]
    set yrange [:300]
    set size square
    set logscale
    set grid
    plot "scatter.txt" using 2:4 title "", x title ""
EOFMarker