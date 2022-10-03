import RsA as rsa
import graphviz

#file to play with whatever I just finished to check basic functionality

#draws the automaton into a pdf using graphviz
def drawAutomaton(aut, name):
    graph = graphviz.Digraph(name)
    graph.node('init_arrow', label = "", shape = 'none')
    for q in aut.Q:
        if q in aut.F:
            graph.node(q, shape = 'doublecircle')
        else:
            graph.node(q)
    for t in aut.delta:
        regAssignment = ''
        for r in t.update.keys():
            regAssignment += r+' <- '+str(t.update[r])+'\n'
        eqText = ''
        if t.eqGuard != set():
            eqText = '\n \'in\' part of ' + str(t.eqGuard)
        diseqText = ''
        if t.diseqGuard != set():
            diseqText = '\n \'in\' not part of ' + str(t.diseqGuard)
        graph.edge(t.orig, t.dest, label = ' ' + t.symbol + eqText + diseqText + '\n' + regAssignment)
    for i in aut.I:
        graph.edge('init_arrow', i)
    graph.render()

dfa = rsa.DRsA({'q1', 'q2', 'q3'}, set(), set(), {'q1'}, {'q2'})
dfa.delta.add(rsa.Transition('q1','0', set(), set(), {},'q1'))
dfa.addTransition(rsa.Transition('q1','1', set(), set(), {},'q2'))
dfa.addTransition(rsa.Transition('q2','0', set(), set(), {},'q3'))
dfa.addTransition(rsa.Transition('q2','1', set(), set(), {},'q2'))
dfa.addTransition(rsa.Transition('q3','0', set(), set(), {},'q2'))
dfa.addTransition(rsa.Transition('q3','1', set(), set(), {},'q2'))

drawAutomaton(dfa, 'dfa')
word = (('1', 0), ('0', 0), ('0', 0))
if dfa.runWord(word):
    print("Accepted")
else:
    print("Rejected")


drsa = rsa.DRsA({'q'}, {'r'}, set(), {'q'}, {'q'})
drsa.addTransition(rsa.Transition('q','a', set(), {'r'}, {'r': {'r','in'}},'q'))

word2 = [('a', 'a'), ('a', 'b'), ('a', 'c'), ('a', 'd')]

drawAutomaton(drsa, 'drsa')
if drsa.runWord(word2):
    print("Accepted")
else:
    print("Rejected")




testTree = rsa.SyntaxTree()
testTree.data = rsa.CONCATENATION
treeA = rsa.SyntaxTree()
treeB = rsa.SyntaxTree()
treeA.data = 'a'
treeA.children = []
treeB.data = 'b'
treeB.children = []
testTree.children = [treeA, treeB]

bigTestTree = rsa.SyntaxTree()
bigTestTree.data = rsa.UNION
bigL = rsa.SyntaxTree()
bigL.data = 'c'
bigL.children = []
bigTestTree.children = [bigL, testTree]

id = rsa.Counter()
testTree.createAutomaton(id)

drawAutomaton(testTree.automaton, 'testAutomaton')

#needs to use the same counter as the previous tree, as it includes that one
bigTestTree.createAutomaton(id)
drawAutomaton(bigTestTree.automaton, 'bigTestAutomaton')

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



