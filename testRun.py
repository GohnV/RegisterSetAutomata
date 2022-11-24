import RsA as rsa
import graphviz
#file to play with whatever I just finished to check basic functionality

class Pair:
    type = ''
    data = ''
    def __init__(self, type, data):
        self.type = type
        self.data = data
    def createPair(self, symbol):
        if symbol in '&|*()$':
            self.type = symbol
            self. data = ''
        else:
            self.type = 'i'
            self.data = symbol

class Pushdown:
    data = []
    def push(self, item):
        for i in item.split():
            self.data.append(i)
    def top(self):
        return self.data[-1]
    def pop(self):
        return self.data.pop(-1)
    def topTerm(self):
        pass



def topTerm(list):
    for i in range(1,len(list)+1):
        if list[-i].type != 'E':
            return list[-i]
def rIndex(list, item):

    for i in range(1,len(list)+1):

        if list[-i].type == item.type:
            return len(list) - i   
    return -1       

def strAfterInd(list, index):
    str = ''
    for i in range(index+1, len(list)):
        if str == '':
            str = list[i].type
        else:
            str = str + ' ' + list[i].type
    return str

def createTree(expr):
    rules = ['E & E','E | E', 'E *', '( E )', 'i']
    dict = {'&':0, '|':1, '*':2, '(':3, ')':4, 'i':5, '$': 6}
    table = [['>', '>', '<', '<', '>', '<', '>'],
             ['<', '>', '<', '<', '>', '<', '>'],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['<', '<', '<', '<', '=', '<', '' ],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['<', '<', '<', '<', '' , '<', '' ]]
    i = 0
    captCount = 0
    pushdown = [Pair('$','')]
    while True:
        a = topTerm(pushdown)
        ai = rIndex(pushdown, a)
        
        b = Pair('','')
        b.createPair(expr[i])
        '''
        print('a = ', a.type,',', 'ai = ', ai, end = ' ')
        print('b = ', b.type)
        print("start:", end=' ')
        for p in pushdown:
            print(p.type, end='')
        print()
        '''    
        #catch KeyError!!!!
        tblSymbol = table[dict[a.type]][dict[b.type]]
        #print("symbol:",tblSymbol)
        if tblSymbol == '=':
            pushdown.append(b)
            i += 1
        elif tblSymbol == '<':
            pushdown.insert(ai+1, Pair('<', ''))
            pushdown.append(b)
            i += 1  
        elif tblSymbol == '>':
            ind = rIndex(pushdown, Pair('<', ''))
            if ind != -1:
                string = strAfterInd(pushdown, ind)
                if string in rules:
                    # Vyrobeni konkretniho malyho stromu
                    #potom priradit strom do dat paru

                    tree= rsa.SyntaxTree()

                    if len(string) == 1:
                        tree.children = []
                        if pushdown[ind+1].data.isnumeric():
                            tree.data = rsa.BACKREFCHAR + pushdown[ind+1].data
                        elif pushdown[ind+1].data == '.':
                            tree.data = rsa.ANYCHAR
                        elif pushdown[ind+1].data == '@':
                            captCount += 1
                            tree.data = rsa.CAPTURECHAR + str(captCount)
                        else:
                            tree.data = pushdown[ind+1].data

                    elif string[0] == '(':
                        tree = pushdown[ind+2].data
                    #Tohle asi predelat, je to humus:
                    elif string[0] == 'E':
                        if string[2] == '*':
                            tree.data = rsa.ITERATION
                            tree.children = [pushdown[ind+1].data]
                        else:
                            tree.children = [pushdown[ind+1].data, pushdown[ind+3].data]
                            if string[2] == '&':
                                tree.data = rsa.CONCATENATION
                            elif string[2] == '|':
                                tree.data = rsa.UNION
                    #Odsataneni polozek ze zasobniku
                    for j in range(ind, len(pushdown)):
                        pushdown.pop(ind)
                    pushdown.append(Pair('E', tree))
                    #print('E ->', str)
                else:
                    print('chyba1')
                    return -1
            else:
                print('chyba2')
                return -1
        else:
            print('chyba3')
            return -1
        #print('i =', i,'expr[i] =', expr[i] )

        '''
        print('end:', end = ' ')
        for p in pushdown:
            print(p.type, end='')
        print()
        ''' 
        if (b.type == '$' and len(pushdown) == 2):
            if pushdown[0].type == '$' and pushdown[1].type == 'E':
                return pushdown[1].data

def strIfMacroState(q):
    ret = q
    if isinstance(q, rsa.MacroState):
        smap = list(q.states)
        smap.sort()
        ret = str(smap)+str(q.mapping.values())
    return ret


#draws the automaton as a pdf using graphviz
def drawAutomaton(aut, name):
    graph = graphviz.Digraph(name) 
    graph.format = 'svg'
    graph.graph_attr["rankdir"] = "LR"
    graph.node('init_arrow', label = "", shape = 'none')
    q_shape = 'octagon'
    f_shape = 'doubleoctagon'
    if isinstance(aut, rsa.NRA):
        q_shape = 'circle'
        f_shape = 'doublecircle'
    eq_op = ' in ∈ '
    diseq_op = ' in ∉ '
    if isinstance(aut, rsa.NRA):
        eq_op = ' in = '
        diseq_op = ' in != '
    for q in aut.Q:
        qname = strIfMacroState(q)
        if q in aut.F:
            graph.node(qname, shape = f_shape)
        else:
            graph.node(qname, shape = q_shape)
    for t in aut.delta:
        regAssignment = ''
        for r in t.update.keys():
            regAssignment += ' '+r+' <- ' + str(t.update[r])+'\n'
        eqText = ''
        for g in t.eqGuard:
            eqText += '\n' + eq_op + str(g)
        diseqText = ''
        for g in t.diseqGuard:
            diseqText +='\n' + diseq_op + str(g)
        sym = t.symbol
        if t.symbol == rsa.EPSILON:
            sym = 'ε'
        elif t.symbol == rsa.ANYCHAR:
            sym = 'Σ'
        oname = strIfMacroState(t.orig)
        dname = strIfMacroState(t.dest)
        graph.edge(oname, dname, label = ' ' + sym + eqText + diseqText + '\n' + regAssignment)
    for i in aut.I:
        iname = strIfMacroState(i)
        graph.edge('init_arrow', iname)
    graph.render()

def createGraph(tree, graph, id):
    graph.node(tree.data+str(id.count))
    currCount = id.count
    for i in range(len(tree.children)):
        id.count += 1 
        graph.edge(tree.data+str(currCount), tree.children[i].data+str(id.count))   
        createGraph(tree.children[i], graph, id)

def drawSyntaxTree(tree, name):
    id = rsa.Counter()
    graph = graphviz.Digraph(name)
    graph.format = 'svg'
    createGraph(tree, graph, id)
    graph.render()

#@-capture character
#&-concatenation
#numbers are backreferences
#parsedTree = createTree('@&.*&;&.*&@&.*&;&.*&@&.*&3&2&1$')
#parsedTree = createTree(".*&a&b&c&.*$")
parsedTree = createTree("@&;&1$")
#parsedTree = createTree("@&a&b&c&1$")


drawSyntaxTree(parsedTree, "parsedTree")
id = rsa.Counter()
parsedTree.createAutomaton(id)
parsedAutomaton = parsedTree.automaton
parsedAutomaton.removeEps()
parsedAutomaton.removeUnreachable()
#drawAutomaton(parsedAutomaton, "parsedAutomaton1")

#parsedAutomaton.completeUpdates()
#drawAutomaton(parsedAutomaton, "parsedAutomaton2")

#parsedAutomaton.makeRegisterLocal()

drawAutomaton(parsedAutomaton, "parsedAutomaton")


detAut = parsedAutomaton.determinize()

drawAutomaton(detAut, "detAutomaton")
if detAut.runWord("a;a"):
    print("accepted")
else:
    print("not accepted")

rep = rsa.NRA({'q', 's', 't'}, {'r'}, set(), {'q'}, {'t'})
rep.addTransition(rsa.Transition('q', rsa.ANYCHAR, set(), set(), {'r':rsa.BOTTOM}, 'q'))
rep.addTransition(rsa.Transition('q', rsa.ANYCHAR, set(), set(), {'r':rsa.IN}, 's'))
rep.addTransition(rsa.Transition('s', rsa.ANYCHAR, set(), set(), {'r':'r'}, 's'))
rep.addTransition(rsa.Transition('s', rsa.ANYCHAR, {'r'}, set(), {'r':rsa.BOTTOM}, 't'))
rep.addTransition(rsa.Transition('t', rsa.ANYCHAR, set(), set(), {'r':rsa.BOTTOM}, 't'))


#rep.completeUpdates
drawAutomaton(rep, "repAutomaton")

detAut2 = rep.determinize()

drawAutomaton(detAut2, "drepAutomaton")
if detAut2.runWord("aa"):
    print("accepted")
else:
    print("not accepted")

'''
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

capt = rsa.SyntaxTree()
backref = rsa.SyntaxTree()
capt.children = []
backref.children = []
capt.data = rsa.CAPTURECHAR+"1"
backref.data = rsa.BACKREFCHAR+"1"

bigL = rsa.SyntaxTree()
bigL.data = rsa.CONCATENATION
bigL.children = [capt, backref]
bigTestTree.children = [bigL, testTree]

biggerTestTree = rsa.SyntaxTree()
biggerTestTree.data = rsa.ITERATION
biggerTestTree.children = [bigTestTree]

id = rsa.Counter()

testTree.createAutomaton(id)
drawAutomaton(testTree.automaton, 'testAutomaton')

#needs to use the same counter as the previous tree, as it includes that one
bigTestTree.createAutomaton(id)
drawAutomaton(bigTestTree.automaton, 'bigTestAutomaton')

biggerTestTree.createAutomaton(id)
biggerTestTree.automaton.removeEps()
biggerTestTree.automaton.removeUnreachable()

drawAutomaton(biggerTestTree.automaton, 'biggerTestAutomaton')

drawSyntaxTree(biggerTestTree, 'biggerTestTree')

exRegex = rsa.SyntaxTree()


exReCon2 = rsa.SyntaxTree()
exReCon2.data = rsa.CONCATENATION
exReCon3 = rsa.SyntaxTree()

exReCon3.data = rsa.CONCATENATION

exReCon4 = rsa.SyntaxTree()
exReCon4.data = rsa.CONCATENATION


exReCapt1 = rsa.SyntaxTree()
exReCapt1.data = rsa.CAPTURECHAR+'2'

exReAnychar2 = rsa.SyntaxTree()
exReAnychar2.data = rsa.ANYCHAR

exReCon3.children = [exReAnychar2]


exReCapt2 = rsa.SyntaxTree()
exReCapt2.data = rsa.CAPTURECHAR+'2'
exReCon3.children = [exReCapt2, exReCon4]

exReIte1 = rsa.SyntaxTree()
exReIte1.data = rsa.ITERATION
exReAnychar1 = rsa.SyntaxTree()
exReAnychar1.data = rsa.ANYCHAR
exReIte1.children = [exReAnychar1]
exReCon2.children = [exReIte1, exReCon3]
exRegex.data = rsa.CONCATENATION
exRegex.children = [exReCapt1, exReCon2]

drawSyntaxTree(exRegex, 'exampleTree')

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

print(str(biggerTestTree.automaton.epsClosure('6')))

if testDRSA.runWord(word3):
    print("Accepted")
else:
    print("Rejected")

'''

