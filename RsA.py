#Author: Jan Vašák, 24.9.2022

#TODO better initialization for SyntaxTree
#TODO syntax tree unique names???

ANYCHAR = "any"
EPSILON = "epsilon"
CONCATENATION = "con"
UNION = "union"
ITERATION = "iter"
IN = "in"
CAPTURECHAR = "capturechar"
BACKREFCHAR = "backrefchar"

#for unique ids for states when creating automata from syntax tree
class Counter:
    count = 0
    def __init__(self):
        count = 0
   

class SyntaxTree:
    data = None
    children = []
    automaton = None
    #id to create a unique name for each state in the automaton
    def createAutomaton(self, id):
        if self.automaton == None:
            if self.children != []:
                for i in self.children:
                    print(i.data)
                    i.createAutomaton(id)
            #actual automaton creation for each node/leaf
            if CAPTURECHAR in self.data:
                id.count += 2
                reg = 'r'+self.data.replace(CAPTURECHAR, "")
                self.automaton = NRA({str(id.count), str(id.count-1)}, {reg}, set(), {str(id.count-1)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count-1), ANYCHAR, set(), set(), {reg:'in'}, str(id.count)))

            elif BACKREFCHAR in self.data:
                id.count += 2
                reg = 'r'+self.data.replace(BACKREFCHAR, "")
                self.automaton = NRA({str(id.count), str(id.count-1)}, {reg}, set(), {str(id.count-1)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count-1), ANYCHAR, {reg}, set(), {}, str(id.count)))

            elif self.children == []:
                id.count += 2
                self.automaton = NRA({str(id.count), str(id.count-1)}, set(), set(), {str(id.count-1)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count-1), self.data, set(), set(), {}, str(id.count)))
            
            elif self.data == CONCATENATION:
                self.automaton = NRA(set(), set(), set(), set(), set())
                self.automaton.importAutomaton(self.children[0].automaton)
                self.automaton.importAutomaton(self.children[1].automaton)
                for i in self.children[0].automaton.I:
                    self.automaton.addI(i)
                for f in self.children[1].automaton.F:
                    self.automaton.addF(f)
                for f in self.children[0].automaton.F:
                    for i in self.children[1].automaton.I:
                        self.automaton.addTransition(Transition(f, EPSILON, set(), set(), {}, i))
            
            elif self.data == UNION:
                id.count += 1
                self.automaton = NRA(set(), set(), set(), set(), set())
                self.automaton.importAutomaton(self.children[0].automaton)
                self.automaton.importAutomaton(self.children[1].automaton)
                for f in self.children[0].automaton.F:
                    self.automaton.addF(f)
                for f in self.children[1].automaton.F:
                    self.automaton.addF(f)
                self.automaton.addQ(str(id.count))
                self.automaton.addI(str(id.count))
                for i in self.children[0].automaton.I:
                    self.automaton.addTransition(Transition(str(id.count), EPSILON, set(), set(), {}, i))
                for i in self.children[1].automaton.I:
                    self.automaton.addTransition(Transition(str(id.count), EPSILON, set(), set(), {}, i))

            elif self.data == ITERATION:
                id.count += 1
                self.automaton = NRA(set(), set(), set(), set(), set())
                self.automaton.importAutomaton(self.children[0].automaton)
                for f in self.children[0].automaton.F:
                    self.automaton.addF(f)
                    for i in self.children[0].automaton.I:
                        self.automaton.addTransition(Transition(f, EPSILON, set(), set(), {}, i))
                self.automaton.addQ(str(id.count))
                self.automaton.addI(str(id.count))
                self.automaton.addF(str(id.count))
                self.automaton.addTransition(Transition(str(id.count), EPSILON, set(), set(), {}, i))

#end of class SyntaxTree


class Transition:
    orig = ''               #original state
    symbol = ''
    eqGuard = set()
    diseqGuard = set()
    update = {}
    dest = ''               #destination state
    def __init__(self, orig, symbol, eqGuard, diseqGuard, update, dest):
        self.orig = orig
        self.symbol = symbol
        self.eqGuard = eqGuard
        self.diseqGuard = diseqGuard
        self.update = update
        self.dest = dest
#end of class Transition

class RsA:
    Q = set()          #set of states
    R = set()          #set of registers
    delta = set()      #set of transitions 
    I = set()          #set of initial states
    F = set()          #set of final states

    def __init__(self, Q, R, delta, I, F):
        self.Q = Q
        self.R = R
        self.delta = delta
        self.I = I
        self.F = F

    #Update Registers
    #   Unspecified registers keep their value
    def updateRegs(self, regConf, up, input):
        for r in regConf.keys():
            tmp = regConf[r]
            if r in up.keys():
                for x in up[r]:
                    if x == IN:
                        tmp.add(input)
                    else:
                        tmp.union(regConf[x])
            regConf.update({r : tmp})

    #copies everything except initial and final states from a different automaton into this one
    def importAutomaton(self, automaton):
        for q in automaton.Q:
            self.addQ(q)
        for r in automaton.R:
            self.addR(r)
        for t in automaton.delta:
            self.addTransition(t)

    #creates epsilon closure for a state in this automaton
    def epsClosure(self, state):
        #FIXME
        #closure and closureNew is the same set, need deep copy I guess
        closure = {state}
        closureNew = closure.copy()
        while True:
            closure = closureNew
            print("run")
            for t in self.delta:
                if t.orig in closureNew and t.symbol == EPSILON:
                    closureNew.add(t.dest)        
            if closure == closureNew:
                break
        return closure

    #removes epsilon transitions
    def removeEps(self):
        pass


    def runWord(self, word):
        print("This would run", word, "over this RsA")

    def addQ(self, q):
        self.Q.add(q)

    def addR(self, reg):
        self.R.add(reg)

    def addTransition(self, t):
        assert isinstance(t, Transition)
        self.delta.add(t)

    def addI(self, i):
        assert i in self.Q
        self.I.add(i)

    def addF(self, f):
        assert f in self.Q
        self.F.add(f)
#end of class RsA
    

class DRsA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    #tests guards of a transition
    def guardTest(self, input, regConf, eqG, diseqG):
        for g in eqG:
            for r in regConf.keys():
                if g == r:
                    if not input in regConf[r]:
                        return False
        for g in diseqG:
            for r in regConf.keys():
                if g == r:
                    if input in regConf[r]:
                        return False
        return True

    #Runs a word on this drsa
    def runWord(self, word):
        regConf = {}
        for r in self.R:
            regConf.update({r : set()})
        c = ''
        assert len(self.I) == 1
        for i in self.I:
            c = i
        for i in word:
            cnt = 0
            for t in self.delta:
                #Add . (anychar) and maybe more stuff
                if t.orig == c and t.symbol == i[0] and self.guardTest(i[1], regConf, t.eqGuard, t.diseqGuard):
                    #assuming there is only one such transition
                    #!
                    c = t.dest
                    self.updateRegs(regConf,t.update, i[1])
                    cnt += 1 
                    break
            if cnt == 0:
                #no possible transition, run dies
                self.clearRegs()
                return False
        if {c}.issubset(self.F):
            return True
        else:
            return False
#end of class DRsA


class NRA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def runWord(self, word):
        print("This would do a nondeterministic run of word", word, "on this NRA")
#end of class NRA