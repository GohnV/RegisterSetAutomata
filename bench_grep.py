import time
import subprocess
import sys

N_EX = 250
N = 1000
BIG_STEP = 10
SAMPLES = 10

regex = ".*&@&.*&1&.*&;&.*&;&.*&1$"
PREF="a"
SUF=";a;a;a"
PUMP = ';'

for n in list(range(1, N_EX+1))+list(range(N_EX, N+1, BIG_STEP)):
    init_len = len(PREF) + len(SUF)
    if n <= init_len:
        word = PREF + SUF[:n-1]
    else:
        word = PREF + (n-init_len)*PUMP + SUF
    total_time = 0
    for i in range(SAMPLES):
        time.sleep(1/1000000.0)
        t0 = time.perf_counter()
        subprocess.run("echo '"+ word+"' | grep -E '^.*(.).*\\1.*;.*;.*\\1$' >/dev/null",shell=True)
        t1 = time.perf_counter()
        total_time += t1-t0
    print(n, total_time/SAMPLES)
    print(n, total_time/SAMPLES, file=sys.stderr)