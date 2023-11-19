#Author: Jan Vašák, 24.9.2022

import itertools as it
import copy

MYEMPTY = (' ', frozenset())
ANYCHAR = ('^', frozenset())
EPSILON = "epsilon"
CONCATENATION = "con"
UNION = "union"
ITERATION = "iter"
IN = "in"
CAPTURECHAR = "capturechar"
BACKREFCHAR = "backrefchar"
BOTTOM = "NULL"
SIGMASTAR = "sstar"

#from itertools recipes
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(len(s)+1))

def myIntersection(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return ('^', t1[1].union(t2[1]))
    elif t1[0] == '^':
        return (' ', t2[1].difference(t1[1]))
    elif t2[0] == '^':
        return (' ', t1[1].difference(t2[1]))
    else:
        return (' ', t1[1].intersection(t2[1]))

def myDifference(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return (' ', t1[1].difference(t1[1].union(t2[1])))
    elif t1[0] == '^':
        return ('^', t1[1].union(t2[1]))
    elif t2[0] == '^':
        return (' ', t2[1].intersection(t1[1]))
    else:
        return (' ', t1[1].difference(t2[1]))

def myIsSubset(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return t2[1].issubset(t1[1])
    elif t1[0] == '^':
        return False
    elif t2[0] == '^':
        return t2[1].isdisjoint(t1[1])
    else:
        return t1[1].issubset(t2[1])

def intersectSets(sets):
    n = len(sets)
    if n >= 1:
        tmp = sets[0]
        for i in range(1, n):
            tmp = myIntersection(tmp, sets[i])
        return tmp
    else:
        return MYEMPTY


def createMinterms(sets):
    #print('CREATING MINTERMS FROMS',sets)
    n = len(sets)
    minterms = set()
    if n == 1:
        minterms = {sets[0]}
    for m in range(n,0, -1):
        #print('n = ', n, 'm = ', m)
        combs = it.combinations(sets, m)
        for c in combs:
            #print(c)
            res = intersectSets(c)
            #print(res)
            if res != MYEMPTY: #only non-empty sets
                minterms.add(res)
                for i in range(n):
                    sets[i] = myDifference(sets[i], res)
    #print(minterms)
    return minterms

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
                    #print(i.data)
                    i.createAutomaton(id)
            #actual automaton creation for each node/leaf
            if CAPTURECHAR in self.data:
                id.count += 2
                reg = 'r'+self.data.replace(CAPTURECHAR, "")
                self.automaton = NRA({str(id.count), str(id.count-1)}, {reg}, set(), {str(id.count-1)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count-1), self.children[0].data, set(), set(), {reg:'in'}, str(id.count)))

            elif BACKREFCHAR in self.data:
                id.count += 2
                reg = 'r'+self.data.replace(BACKREFCHAR, "")
                self.automaton = NRA({str(id.count), str(id.count-1)}, {reg}, set(), {str(id.count-1)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count-1), ANYCHAR, {reg}, set(), {}, str(id.count)))

            elif SIGMASTAR == self.data:
                id.count += 1
                self.automaton = NRA({str(id.count)}, set(), set(), {str(id.count)}, {str(id.count)})
                self.automaton.addTransition(Transition(str(id.count), ANYCHAR, set(), set(), {}, str(id.count)))

            elif self.children == []:
                id.count += 2
                if not isinstance(self.data, tuple):
                    self.data = (' ',frozenset({self.data}))
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
                if len(self.children[0].automaton.delta) == 1:
                    symbol = (list(self.children[0].automaton.delta))[0].symbol
                    eqGuard = (list(self.children[0].automaton.delta))[0].eqGuard
                    diseqGuard = (list(self.children[0].automaton.delta))[0].diseqGuard
                    update = (list(self.children[0].automaton.delta))[0].update
                    id.count += 1
                    self.automaton = NRA({str(id.count)}, set(), set(), {str(id.count)}, {str(id.count)})
                    self.automaton.addTransition(Transition(str(id.count), symbol, eqGuard, diseqGuard, update, str(id.count)))
                else:
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
    def __init__(self, orig, symbol, eqGuard, diseqGuard, update, dest):
        self.orig = orig
        self.symbol = symbol
        self.eqGuard = eqGuard
        self.diseqGuard = diseqGuard
        self.update = update
        self.dest = dest
#end of class Transition

class MacroState:
    def __init__(self):
        self.states = set()
        self.mapping = {}


class RsA:
    def __init__(self, Q, R, delta, I, F):
        self.Q = Q
        self.R = R
        self.delta = delta
        self.I = I
        self.F = F

    #returns the set of registers active in a given state
    def activeRegs(self, state):
        regs = set()
        for t in self.delta:
            if t.dest == state:
                for r in t.update.keys():
                    if t.update[r] != BOTTOM:
                        regs.add(r)
            if t.orig == state:
                regs = regs.union(t.eqGuard)
                regs = regs.union(t.diseqGuard)
        return regs

    #copies everything except initial and final states from a different automaton into this one
    def importAutomaton(self, automaton):
        for q in automaton.Q:
            self.addQ(q)
        for r in automaton.R:
            self.addR(r)
        for t in automaton.delta:
            self.addTransition(t)

    #Joins states which only have eps or self transitions into another state
    #FIXME: might have a bug if there are multiple eps transitions coming out of the origin state of the removed transition
    def joinStates(self): 
        q_del = set()
        t_del = set()
        t_add = set()
        for q in self.Q:
            found = False
            in_eps = 0
            for t in self.delta:
                if t.dest == q and t.symbol == EPSILON and t.orig != q:
                    if found:
                        found = False
                        break
                    in_eps = t
                    found = True
            if not found:
                continue
            #found only on in epsilon transition
            out_eps = []
            self_t = []
            for t in self.delta:
                if t.orig == q:
                    if t.symbol == EPSILON:
                        out_eps.append(t)
                    elif t.dest == q:
                        self_t.append(t)
                    else:
                        found = False
                        break
            if not found:
                continue
            #join q into origin state of transition in_eps
            q_new = in_eps.orig
            q_del.add(q)
            self.delta.remove(in_eps)
            if q in self.F:
                self.F.remove(q)
                self.F.add(q_new)
            for st in self_t:
                t_del.add(st)
                t_add.add(Transition(q_new, st.symbol, st.eqGuard, st.diseqGuard, st.update, q_new))
            for oe in out_eps:
                t_del.add(oe)
                t_add.add(Transition(q_new, EPSILON, oe.eqGuard, oe.diseqGuard, oe.update, oe.dest))
        for q in q_del:
            self.Q.remove(q)
        for t in t_del:
            self.delta.remove(t)
        for t in t_add:
            self.delta.add(t)
  
    #creates epsilon closure for a state in this automaton
    def epsClosure(self, state):
        closure = {state}
        while True:
            changed = False
            for t in self.delta:
                if t.orig in closure and t.symbol == EPSILON:
                    if t.dest not in closure:
                        closure.add(t.dest)
                        changed = True        
            if not changed:
                break
        return closure

    #removes epsilon transitions
    def removeEps(self):
        deltaNew = set()
        newF = set()
        for q in self.Q:
            epsClos = self.epsClosure(q)
            if not epsClos.isdisjoint(self.F):
                newF.add(q)
            for t in self.delta:
                if t.orig in epsClos and t.symbol != EPSILON:
                    deltaNew.add(Transition(q, t.symbol, t.eqGuard, t.diseqGuard, t.update, t.dest))
        self.delta = deltaNew
        self.F = newF
    
    def removeUnreachable(self):
        newQ = set().union(self.I)
        newDelta = set()
        while True:
            changed = False
            for t in self.delta:
                if (t.orig in newQ):
                    newDelta.add(t)
                    if t.dest not in newQ:
                        newQ.add(t.dest)
                        changed = True
            if not changed:
                break
        self.Q = newQ
        self.delta = newDelta

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

    #Update Registers
    #   Unspecified registers lose their value!
    def updateRegs(self, regConf, up, input):
        newConf = {}
        for r in regConf.keys():
            tmp = set()
            if r in up.keys():
                for y in up[r]:
                    if y == IN:
                        tmp.add(input)
                    else:
                        tmp = tmp.union(regConf[y])
            newConf[r] = tmp
        return newConf
            
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
        #default reg config
        regConf = {}
        for r in self.R:
            regConf.update({r : set()})
        c = ''
        #only 1 initial state
        assert len(self.I) == 1
        for i in self.I:
            c = i
        for s in word:
            #print(c.states, str(c.mapping), end='')
            #print('--', end='')
            cnt = 0
            for t in self.delta:
                if t.symbol[0] == '^':
                    symTest = s not in t.symbol[1]
                else:
                    symTest = s in t.symbol[1]

                if t.orig.states == c.states and t.orig.mapping == c.mapping and symTest and self.guardTest(s, regConf, t.eqGuard, t.diseqGuard):
                    #print(t.symbol,'->', end=' ')
                    c = t.dest
                    regConf = self.updateRegs(regConf,t.update, s)
                    cnt += 1 
                    break
            if cnt == 0:
                #run dies
                return False
            #print(c.states)
        for f in self.F:
            if c.states == f.states and c.mapping == f.mapping:
                return True
        else:
            return False
#end of class DRsA



class NRA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def empty():
        return NRA(set(), set(), set(), set(), set())

    def runWord(self, word):
        print("This would do a nondeterministic run of word", word, "on this NRA")

    def completeUpdates(self):
        deltaNew = set()
        for t in self.delta:
            tNew = Transition(t.orig, t.symbol, t.eqGuard, t.diseqGuard, {}, t.dest)
            for r in self.R:
                if r not in t.update.keys():
                    isIn = False
                    isOut = False
                    for t1 in self.delta:
                        if t1.orig == t.dest:
                            isOut = True
                        if t1.dest == t.orig:
                            isIn = True
                    if isIn and isOut:
                        tNew.update[r] = r
                    else:
                        tNew.update[r] = BOTTOM
                else:
                    tNew.update[r] = t.update[r]
            deltaNew.add(tNew)
        self.delta = deltaNew

    def fillWithBottom(self):
        for t in self.delta:
            for r in self.R:
                if r not in t.update.keys():
                    t.update[r] = BOTTOM

    def cRoofOld(self, x, g, c, check):
        if x in self.R.difference(g):
            return c[x]
        if x in g:
            if check:
                return 1
            return 0
        if x == 'in':
            return 1

    def cRoof(self, x, g, c):
        if x in self.R.difference(g):
            return c[x]
        if x in g:
            return 0
        if x == 'in':
            return 1

    def makeRegisterLocal(self):
        RNew = set()
        for t in self.delta:
            upNew = {}
            eqNew = set()
            diseqNew = set()
            for r in t.update.keys():
                if t.update[r] != BOTTOM:
                    rNew = str(t.dest)+str(r)
                    rUpNew = t.update[r]
                    if (t.update[r] != IN):
                        rUpNew = str(t.orig)+str(t.update[r])
                    upNew[rNew] = rUpNew
                    RNew.add(rNew)
                    if (rUpNew != IN):
                        RNew.add(rUpNew)
            for r in t.eqGuard:
                rNew = str(t.orig)+str(r)
                eqNew.add(rNew)
                RNew.add(rNew)
            for r in t.diseqGuard:
                rNew = str(t.orig)+str(r)
                diseqNew.add(rNew)
                RNew.add(rNew)
            t.update = upNew
            t.eqGuard = eqNew
            t.diseqGuard = diseqNew
        self.R = RNew

    def preprocess(self):
        Inew = set()
        Qnew = set()
        Fnew = set()
        deltanew = set()
        Rnew = set()
        worklist = list()  
        for q in self.I:
            P = (q, frozenset())
            Inew.add(P)
            Qnew.add(P)
            worklist.append(P)
        while worklist != list():
            (q, P) = worklist.pop(0)
            Cbot = set()
            for r in self.R:
                found = False
                for C in P:
                    if r in C:
                        found = True
                        break
                if not found:
                    Cbot.add(r)
            for t in self.delta:
                if t.orig != q or not (Cbot.isdisjoint(t.eqGuard)):
                    continue
                Pnew = set()
                for r in self.R:
                    if t.update[r] == BOTTOM or t.update[r] in Cbot:
                        continue
                    PnewIter = copy.deepcopy(Pnew)
                    found = False
                    for Cnew in PnewIter:
                        Cnew = set(Cnew)
                        for r1 in Cnew:
                            condOneThree = (t.update[r] == t.update[r1] or
                                (t.update[r] in t.eqGuard.union({IN}) and
                                 t.update[r1] in t.eqGuard.union({IN})))
                            condTwo = False
                            for C in P:
                                if (t.update[r] in C and t.update[r1] in C):
                                    condTwo = True
                                    break
                            #TODO: check this
                            if condOneThree or condTwo:
                                Pnew.remove(frozenset(Cnew))
                                Cnew.add(r)
                                Pnew.add(frozenset(Cnew))
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        Pnew.add(frozenset({r}))
                # CnewBot = set()
                # for r in self.R:
                #     found = False
                #     for Cnew in Pnew:
                #         if r in Cnew:
                #             found = True
                #             break
                #     if not found:
                #         CnewBot.add(r)
                if (t.dest, frozenset(Pnew)) not in Qnew:
                    Qnew.add((t.dest, frozenset(Pnew)))
                    worklist.append((t.dest, frozenset(Pnew)))
                #guards
                eqNew = set()
                diseqNew = set()
                for C in P:
                    for r in C:
                        if r in t.eqGuard:
                            eqNew.add(C)
                        if r in t.diseqGuard:
                            diseqNew.add(C)
                #update:
                upNew = {}
                # if CnewBot != set():
                #     upNew = {frozenset(CnewBot): BOTTOM}
                #     Rnew = Rnew.union(Pnew.union({frozenset(CnewBot)}))
                for Cnew in Pnew:
                    found = False
                    tmp = set()#TODO: only here to check errors
                    for r in Cnew:
                        if t.update[r] == IN:
                            found = True
                            tmp = IN
                            break
                    if not found:
                        for C in P:
                            if t.update[list(Cnew)[0]] in C:
                                tmp = C
                                break
                    upNew[Cnew] = tmp
                deltanew.add(Transition((t.orig, P), t.symbol, eqNew, diseqNew, upNew, (t.dest, frozenset(Pnew))))
        for (q, P) in Qnew:
            if q in self.F:
                Fnew.add((q, P))
        self.Q = Qnew
        self.I = Inew
        self.F = Fnew
        self.R = Rnew
        self.delta = deltanew


    def determinize(self):
        #fill in implicit updates
        self.completeUpdates()
        self.makeRegisterLocal()
        self.fillWithBottom()
        #self.preprocess()
        newA = DRsA(set(), self.R, set(), set(), set())
        worklist = [] 
        #Q′ ← worklist ← I′ ← {(I, c0 = {r → 0 | r ∈ R})}:
        temp = MacroState()
        for i in self.I:    
            temp.states.add(i)
        for r in self.R:
            temp.mapping.update({r:0})
        worklist.append(temp)
        newA.Q.add(temp)
        newA.I.add(temp)
        while worklist != []:
            sc = worklist.pop(-1)
            #print(sc.states)
            #FIXME: create minterms of all transitions used in a given set of states into A
            #set A includes all symbols used in transitions
            #to avoid looping through the (infinite) alphabet
            sets = set()
            for t in self.delta:
                if t.orig in sc.states:
                    sets.add(t.symbol)
            A = createMinterms(list(sets))
            regs = set()
            #R[S] \ {r ∈ R | c(r) = 0}:
            for q in sc.states:
                rq = self.activeRegs(q)
                for r in rq:
                    if sc.mapping[r] != 0:
                        regs.add(r)
            G = set(powerset(regs))
            for a in A:
                for g in G:
                    T = set()
                    S1 = set()
                    #T ← {q -[a | g=, g!=, ·]-> q′ ∈ ∆ | q ∈ S, g= ⊆ g, g!= ∩ g = ∅}:
                    for t in self.delta:       #TODO:or t.symbol == ANYCHAR FIXME: remove anychar after minterms are done
                                                #????a in t.symbol[1]???? (in used as a subset operator)
                        #print(a, t.symbol, myIsSubset(a, t.symbol))
                        if (t.orig in sc.states) and myIsSubset(a, t.symbol) and (t.eqGuard.issubset(g))\
                        and (t.diseqGuard.isdisjoint(g)):
                            T.add(t)
                    #S′ ← {q′ | · -[· | ·, ·, ·]-> q′ ∈ T }:
                    for t in T:
                        S1.add(t.dest)
                    for t in T:
                        for r in t.diseqGuard:
                            if sc.mapping[r] == 2:
                                return -1 #?
                    T1 = set()
                    #create t^\bullet
                    for t in T:
                        for r in t.update.keys():
                            if t.update[r] in t.eqGuard:
                                t.update[r] = IN
                        T1.add(t)
                    op = {}
                    for ri in self.R:
                        tmp = set()
                        for t in T1:
                            #"line" 13:
                            if t.update[ri] != BOTTOM and (t.update[ri] == IN or sc.mapping[t.update[ri]] != 0):
                                tmp.add(t.update[ri])
                        if not tmp.isdisjoint(g):
                            op[ri] = tmp.difference({IN})
                        else:
                            op[ri] = tmp
                    
                    #'''
                    #lines 16-19 FIXME:prints
                    #print("=========", S1, g, "===========")
                    for q1 in S1:
                        P = [[]]
                        Rq1 = set()
                        for r in self.activeRegs(q1):
                            Rq1.add(r)

                        #cartesian product
                        for ri in Rq1:
                            #print('ri = ', ri, 'op(ri) = ',op[ri])
                            Pnew = []
                            for elem in P:
                                for rup in op[ri]:
                                    tmp = copy.deepcopy(elem)
                                    tmp.append([ri, rup])
                                    Pnew.append(tmp)
                            P = Pnew
                        #print("         q1 =", q1, "R[q1] =", Rq1, "P =", P)
                        for elem in P:
                            found_conf = False
                            #print(elem)
                            for t in T1:
                                if t.dest == q1:
                                    #print(t.orig,"->", t.dest,"| up =", t.update)
                                    con = True
                                    for xi in elem:
                                        #check eq.
                                        if t.update[xi[0]] != xi[1]:
                                            #print(xi[0], xi[1], t.update[xi[0]])
                                            con = False
                                            break
                                    if con:
                                        #print("Found:",t.orig,"->", t.dest,"| up =", t.update)
                                        found_conf = True
                                        break
                            if not found_conf:
                                return -1
                    #'''

                    #up′ ← {r_i → op_ri | r_i ∈ R}:
                    up1 = {}
                    c1 = {}
                    for ri in self.R:
                        up1[ri] = op[ri]
                    #line 15, c' = SUM(x in op_ri, c(x)):
                    for ri in self.R:
                        cnt = 0
                        for x in up1[ri]:
                            c_aux = 0
                            if x == IN:
                                c_aux = 1
                            else:
                                c_aux = sc.mapping[x]
                            cnt += c_aux
                            if cnt > 2:
                                cnt = 2
                        c1[ri] = cnt
                    s1c1 = MacroState()
                    s1c1.states = S1
                    s1c1.mapping = c1
                    found = False
                    for q1 in newA.Q:
                        #orig:
                        if s1c1.states == q1.states and s1c1.mapping == q1.mapping:
                            found = True
                            break
                    if not found:
                        worklist.append(s1c1)
                        newA.addQ(s1c1)
                    newA.addTransition(Transition(sc, a, g, self.R.difference(g), up1, s1c1))
        #accepting states:
        for mq in newA.Q:
            for q in mq.states:
                if q in self.F:
                    newA.addF(mq)
                    break
        return newA

    def determinizeOld(self):
        #fill in implicit updates
        self.completeUpdates()
        self.makeRegisterLocal()        
        self.fillWithBottom()       
        newA = DRsA(set(), self.R, set(), set(), set())
        worklist = [] 
        #Q′ ← worklist ← I′ ← {(I, c0 = {r → 0 | r ∈ R})}:
        temp = MacroState()
        for i in self.I:    
            temp.states.add(i)
        for r in self.R:
            temp.mapping.update({r:0})
        worklist.append(temp)
        newA.Q.add(temp)
        newA.I.add(temp)
        while worklist != []:
            sc = worklist.pop(-1)                 
            A = set()
            #set A includes all symbols used in transitions
            #to avoid looping through the (infinite) alphabet
            for t in self.delta:
                if t.orig in sc.states:
                    A.add(t.symbol)
            regs = set()
            #R[S] \ {r ∈ R | c(r) = 0}:
            for q in sc.states:
                rq = self.activeRegs(q)
                for r in rq:
                    if sc.mapping[r] != 0:
                        regs.add(r)
            G = set(powerset(regs))
            for a in A:
                for g in G:
                    check = False
                    T = set()
                    S1 = set()
                    #T ← {q -[a | g=, g!=, ·]-> q′ ∈ ∆ | q ∈ S, g= ⊆ g, g!= ∩ g = ∅}:
                    for t in self.delta:       #TODO:or t.symbol == ANYCHAR
                        if (t.orig in sc.states) and (t.symbol == a or t.symbol == ANYCHAR) and (t.eqGuard.issubset(g))\
                        and (t.diseqGuard.isdisjoint(g)):
                            T.add(t)
                    #S′ ← {q′ | · -[· | ·, ·, ·]-> q′ ∈ T }:
                    for t in T:
                        S1.add(t.dest)
                    for t in T:
                        for r in t.diseqGuard:
                            if sc.mapping[r] == 2:
                                return -1 #?
                    op = {}
                    for ri in self.R:
                        tmp = set()    
                        for t in T:
                            #"line" 12:
                            x = set()
                            if t.update[ri] in self.R.union({IN}) and (t.update[ri] == IN or sc.mapping[t.update[ri]] != 0) and t.update[ri] not in t.diseqGuard:
                                x = {t.update[ri]}
                            elif t.update[ri] in t.eqGuard:
                                x = {IN}
                            tmp = tmp.union(x)
                        if not tmp.isdisjoint(g):
                            op[ri] = tmp.difference({IN})
                            check = True
                        else:
                            op[ri] = tmp
                    for q1 in S1:
                        P = set()
                        for r in self.activeRegs(q):
                            #lines 15-17!!!
                            pass
                    #up′ ← {r_i → op_ri | r_i ∈ R}:
                    up1 = {}
                    for ri in self.R:
                        up1[ri] = op[ri]
                    c1 = {}
                    #line 19:
                    for ri in self.R:
                        cnt = 0
                        for x in up1[ri]:
                            cnt += self.cRoofOld(x, g, sc.mapping, check)
                            if cnt > 2:
                                cnt = 2
                        c1[ri] = cnt
                    s1c1 = MacroState()
                    s1c1.states = S1
                    s1c1.mapping = c1
                    found = False
                    for q1 in newA.Q:
                        #orig:
                        if s1c1.states == q1.states and s1c1.mapping == q1.mapping:
                            found = True
                            break
                    if not found:
                        worklist.append(s1c1)
                        newA.addQ(s1c1)
                    newA.addTransition(Transition(sc, a, g, self.R.difference(g), up1, s1c1))
        #accepting states:
        for mq in newA.Q:
            for q in mq.states:
                if q in self.F:
                    newA.addF(mq)
                    break
        return newA

                        
#end of class NRA