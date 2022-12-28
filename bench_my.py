import RsA as rsa
import rsa_utils as ru
import time

N = 1000
SAMPLES = 10

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

for n in range(1, N+1):
    init_len = len(PREF) + len(SUF)
    if n <= init_len:
        word = PREF + SUF[:n-1]
    else:
        word = PREF + (n-init_len)*PUMP + SUF
    total_time = 0
    for i in range(SAMPLES):
        t0 = time.time()
        res = detAut.runWord(word)
        t1 = time.time()
        total_time += t1-t0
    print(total_time/SAMPLES)
