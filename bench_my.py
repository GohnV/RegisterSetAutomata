import RsA as rsa
import rsa_utils as ru
import time
import sys

N_EX = 250
N = 1000
BIG_STEP = 10
SAMPLES = 20

regex = ".*&@&.*&1&.*&;&.*&;&.*&1$"
#       ^.*(.).*\1 .* ; .* ; .*\1$

parsedTree = ru.createTree(regex)
ru.drawSyntaxTree(parsedTree, "parsedTree")
id = rsa.Counter()
parsedTree.createAutomaton(id)
parsedAutomaton = parsedTree.automaton
parsedAutomaton.joinStates()
parsedAutomaton.removeEps()
parsedAutomaton.removeUnreachable()

detAut = parsedAutomaton.determinize()

PREF="a"
SUF=";a;a;a"
PUMP = ';'

for n in list(range(1, N_EX+1))+list(range(N_EX+BIG_STEP, N+1, BIG_STEP)):
    init_len = len(PREF) + len(SUF)
    if n <= init_len:
        word = PREF + SUF[:n-1]
    else:
        word = PREF + (n-init_len)*PUMP + SUF
    total_time = 0
    for i in range(SAMPLES):
        time.sleep(1/1000000.0)
        t0 = time.process_time()
        res = detAut.runWord(word)
        t1 = time.process_time()
        total_time += (t1-t0)
    print(n, total_time/SAMPLES)
    #print(word, file=sys.stderr)
    print(n, total_time/SAMPLES, file=sys.stderr)
