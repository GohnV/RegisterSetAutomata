#!/bin/bash
OUT='graph.svg'
MY='my.txt'
GREP='grep.txt'

#python3 ./bench_my.py >$MY
#python3 ./bench_grep.py >$GREP

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