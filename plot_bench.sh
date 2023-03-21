#!/bin/bash
OUT='graph.pdf'
DIR='mys03-results/'
MY='rsa.txt'
MY_DET='rsa_det.txt'
GREP='grep.txt'

OUT="$DIR""$OUT"
DET_OUT="$DIR""graph_det.pdf"
SP_OUT="$DIR""scatter.pdf"
SP_DET_OUT="$DIR""scatter_det.pdf"

GREP="$DIR""$GREP"
MY="$DIR""$MY"
MY_DET="$DIR""$MY_DET"
SCATTER="$DIR""scatter.txt"
SCATTER_DET="$DIR""scatter_det.txt"


#python3 ./bench_my.py >$MY
#python3 ./bench_grep.py >$GREP

awk '{getline f1 < '\""$GREP"\"'; $2 = $2 OFS f1; print}' "$MY" > "$SCATTER"

gnuplot -persist <<-EOFMarker
    set terminal pdf
    set output "$OUT"

    set multiplot

    set ylabel "Time (s)" font ",18"
    set xlabel "Input length" font ",18"
    set logscale y
    set grid

    plot "$MY" title "RsA implementation" with lines linestyle 1, "$GREP" title "grep" with lines linestyle 2
EOFMarker

gnuplot -persist <<-EOFMarker
    set terminal pdf
    set output "$SP_OUT"

    set multiplot
    set ylabel "grep time (s)" font ",18"
    set xlabel "RsA time (s)" font ",18"
    set xrange [0.0002:2000]
    set yrange [0.0002:2000]
    set size square
    set logscale
    set grid
    plot "$SCATTER" using 2:4 title "", x lt -1 title ""
EOFMarker

awk '{getline f1 < '\""$GREP"\"'; $2 = $2 OFS f1; print}' "$MY_DET" > "$SCATTER_DET"
gnuplot -persist <<-EOFMarker
    set terminal pdf
    set output "$DET_OUT"

    set multiplot

    set ylabel "Time (s)" font ",18"
    set xlabel "Input length" font ",18"
    set logscale y
    set grid

    plot "$MY_DET" title "RsA implementation" with lines linestyle 1, "$GREP" title "grep" with lines linestyle 2
EOFMarker

gnuplot -persist <<-EOFMarker
    set terminal pdf
    set output "$SP_DET_OUT"    

    set multiplot
    set ylabel "grep time (s)" font ",18"
    set xlabel "RsA time (s)" font ",18"
    set xrange [0.0002:2000]
    set yrange [0.0002:2000]
    set size square
    set logscale
    set grid
    plot "$SCATTER_DET" using 2:4 title "", x lt -1 title ""
EOFMarker