import time
import subprocess

N = 1000
SAMPLES = 10

regex = ".*&@&.*&1&.*&;&.*&;&.*&1$"
PREF="a"
SUF=";a;a;a"
PUMP = ';'

for n in range(1, N+1):
    init_len = len(PREF) + len(SUF)
    if n <= init_len:
        word = PREF + SUF[:n-1]
    else:
        word = PREF + (n-init_len)*PUMP + SUF
    total_time = 0
    for i in range(SAMPLES):
        t0 = time.time()
        subprocess.run("echo '"+ word+"' | grep -E '^.*(.).*\\1.*;.*;.*\\1$' >/dev/null",shell=True)
        t1 = time.time()
        total_time += t1-t0
    print(total_time/SAMPLES)
