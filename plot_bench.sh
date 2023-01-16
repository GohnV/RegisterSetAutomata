#!/bin/bash
OUT='graph.svg'
DIR='mys03-results/'
MY='rsa.txt'
MY_DET='rsa_det.txt'
GREP='grep.txt'

OUT="$DIR""$OUT"
DET_OUT="$DIR""graph_det.svg"
SP_OUT="$DIR""scatter.svg"
SP_DET_OUT="$DIR""scatter_det.svg"

GREP="$DIR""$GREP"
MY="$DIR""$MY"
MY_DET="$DIR""$MY_DET"
SCATTER="$DIR""scatter.txt"
SCATTER_DET="$DIR""scatter_det.txt"


#python3 ./bench_my.py >$MY
#python3 ./bench_grep.py >$GREP

awk '{getline f1 < '\""$GREP"\"'; $2 = $2 OFS f1; print}' "$MY" > "$SCATTER" #FIXME:file names and sizes

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "$OUT"

    set multiplot

    set ylabel "Time (s)" font ",18"
    set xlabel "Input length" font ",18"
    set logscale y
    set grid

    plot "$MY" title "RsA implementation" with lines linestyle 1, "$GREP" title "grep" with lines linestyle 2
EOFMarker

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "$SP_OUT"

    set multiplot

    set ylabel "grep time (s)" font ",18"
    set xlabel "RsA time (s)" font ",18"
    set xrange [0.00001:300]
    set yrange [0.00001:300]
    set size square
    set logscale
    set grid
    plot "$SCATTER" using 2:4 title "", x title ""
EOFMarker

awk 'NR<=296 {getline f1 < '\""$GREP"\"'; $2 = $2 OFS f1; print}' "$MY_DET" > "$SCATTER_DET" #FIXME:file names and sizes

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "$DET_OUT"

    set multiplot

    set ylabel "Time (s)" font ",18"
    set xlabel "Input length" font ",18"
    set logscale y
    set grid

    plot "$MY_DET" title "RsA implementation" with lines linestyle 1, "$GREP" title "grep" with lines linestyle 2
EOFMarker

gnuplot -persist <<-EOFMarker
    set terminal svg
    set output "$SP_DET_OUT"    

    set multiplot

    set ylabel "grep time (s)" font ",18"
    set xlabel "RsA time (s)" font ",18"
    set xrange [0.00001:300]
    set yrange [0.00001:300]
    set size square
    set logscale
    set grid
    plot "$SCATTER_DET" using 2:4 title "", x title ""
EOFMarker