import RsA as rsa

#file to play with whatever I just finished to check basic functionality

dfa = rsa.DRsA({'q1', 'q2', 'q3'}, list(), set(), {'q1'}, {'q2'})
dfa.delta.add(rsa.Transition('q1','0', list(), set(), set(),'q1'))
dfa.addTransition(rsa.Transition('q1','1', list(), set(), set(),'q2'))
dfa.addTransition(rsa.Transition('q2','0', list(), set(), set(),'q3'))
dfa.addTransition(rsa.Transition('q2','1', list(), set(), set(),'q2'))
dfa.addTransition(rsa.Transition('q3','0', list(), set(), set(),'q2'))
dfa.addTransition(rsa.Transition('q3','1', list(), set(), set(),'q2'))


word = (('1', 0), ('0', 0), ('0', 0))
if dfa.runWord(word):
    print("Accepted")
else:
    print("Rejected")


drsa = rsa.DRsA({'q'}, {'r'}, set(), {'q'}, {'q'})
drsa.addTransition(rsa.Transition('q','a', set(), {'r'}, {'r': {'r','in'}},'q'))

word2 = [('a', 'a'), ('a', 'b'), ('a', 'c'), ('a', 'd')]

if drsa.runWord(word2):
    print("Accepted")
else:
    print("Rejected")



testTree = rsa.SyntaxTree()
testTree.data = "con"
treeA = rsa.SyntaxTree()
treeB = rsa.SyntaxTree()
treeA.data = 'a'
treeA.children = []
treeB.data = 'b'
treeB.children = []
testTree.children = [treeA, treeB]
count = rsa.Counter()
testTree.createAutomaton(count)
print(testTree.automaton.Q)
print(testTree.automaton.R)
for t in testTree.automaton.delta:
    print(t.orig,"---",t.symbol,"-->",t.dest)
print(testTree.automaton.I)
print(testTree.automaton.F)
testDRSA = rsa.DRsA(set(), list(), set(), set(), set())
for q in testTree.automaton.Q:
    testDRSA.addQ(q)
for r in testTree.automaton.R:
    testDRSA.addR(r)
for t in testTree.automaton.delta:
    testDRSA.addTransition(t)
for i in testTree.automaton.I:
    testDRSA.addI(i)
for f in testTree.automaton.F:
    testDRSA.addF(f)
word3 = [('a', 'a'), ("epsilon", 'b'), ('b', 'c')]

if testDRSA.runWord(word3):
    print("Accepted")
else:
    print("Rejected")



