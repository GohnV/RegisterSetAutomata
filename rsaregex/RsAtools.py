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
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(len(s)+1))

def rsa_set_add_char(my_set: tuple, char: str):
    my_set_neg, my_set_set = my_set
    my_set_set = set(my_set_set)
    if my_set_neg == '^':
        my_set_set.discard(char)
    elif my_set_neg == ' ':
        my_set_set.add(char)
    return my_set_neg, frozenset(my_set_set)

def rsa_set_remove_char(my_set: tuple, char: str):
    my_set_neg, my_set_set = my_set
    my_set_set = set(my_set_set)
    if my_set_neg == '^':
        my_set_set.add(char)
    elif my_set_neg == ' ':
        my_set_set.discard(char)
    return my_set_neg, frozenset(my_set_set)

def rsa_set_union(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return ('^', t1[1].intersection(t2[1]))
    elif t1[0] == '^':
        return ('^', t1[1].difference(t2[1]))
    elif t2[0] == '^':
        return ('^', t2[1].difference(t1[1]))
    else:
        return (' ', t1[1].union(t2[1]))

def rsa_set_intersection(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return ('^', t1[1].union(t2[1]))
    elif t1[0] == '^':
        return (' ', t2[1].difference(t1[1]))
    elif t2[0] == '^':
        return (' ', t1[1].difference(t2[1]))
    else:
        return (' ', t1[1].intersection(t2[1]))

def rsa_set_difference(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return (' ', t2[1].difference(t1[1]))
    elif t1[0] == '^':
        return ('^', t1[1].union(t2[1]))
    elif t2[0] == '^':
        return (' ', t2[1].intersection(t1[1]))
    else:
        return (' ', t1[1].difference(t2[1]))

def rsa_is_subset(t1, t2):
    if t1[0] == '^' and t2[0] == '^':
        return t2[1].issubset(t1[1])
    elif t1[0] == '^':
        return False
    elif t2[0] == '^':
        return t2[1].isdisjoint(t1[1])
    else:
        return t1[1].issubset(t2[1])
    
def rsa_is_char_in(char, t):
    neg, char_set = t
    if neg == '^':
        return char not in char_set
    else:
        return char in char_set


def rsa_intersect_n_sets(sets):
    '''intersects all sets specified in param sets'''
    n = len(sets)
    if n >= 1:
        tmp = sets[0]
        for i in range(1, n):
            tmp = rsa_set_intersection(tmp, sets[i])
        return tmp
    else:
        return MYEMPTY


def _create_minterms(sets):
    #print('CREATING MINTERMS FROMS',sets)
    n = len(sets)
    minterms = set()
    if n == 1:
        minterms = {sets[0]}
    for m in range(n,0, -1):
        #print('n = ', n, 'm = ', m)
        combs = it.combinations(sets, m)
        for c in combs:
            #print("c =",c)
            res = rsa_intersect_n_sets(c)
            #print("res =", res)
            if res != MYEMPTY: #only non-empty sets
                minterms.add(res)
                for i in range(n):
                    sets[i] = rsa_set_difference(sets[i], res)
    #print(minterms)
    return minterms

class Transition:
    """! Class representing a transition
    """
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
    """ Class representing an RsA.
    """

    def __init__(self, Q, R, delta, I, F):
        self.Q = Q
        self.R = R
        self.delta = delta
        self.I = I
        self.F = F

    #returns the set of registers active in a given state
    def _active_regs(self, state):
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

    def import_automaton(self, automaton):
        '''copies everything except initial
        and final states from a different automaton into this one'''
        for q in automaton.Q:
            self.add_q(q)
        for r in automaton.R:
            self.add_r(r)
        for t in automaton.delta:
            self.add_transition(t)
  
    def eps_closure(self, state):
        """ creates epsilon closure for a state in this automaton
        """
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

    def remove_eps(self):
        '''removes epsilon transitions'''
        deltaNew = set()
        newF = set()
        for q in self.Q:
            epsClos = self.eps_closure(q)
            if not epsClos.isdisjoint(self.F):
                newF.add(q)
            for t in self.delta:
                if t.orig in epsClos and t.symbol != EPSILON:
                    deltaNew.add(Transition(q, t.symbol, t.eqGuard, t.diseqGuard, t.update, t.dest))
        self.delta = deltaNew
        self.F = newF
    
    def remove_unreachable(self):
        '''removes unreachable states'''
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

    def run_word(self, word):
        raise NotImplementedError

    def add_q(self, q):
        self.Q.add(q)

    def add_r(self, reg):
        self.R.add(reg)

    def add_transition(self, t):
        assert isinstance(t, Transition)
        self.delta.add(t)

    def add_i(self, i):
        assert i in self.Q
        self.I.add(i)

    def add_f(self, f):
        assert f in self.Q
        self.F.add(f)
#end of class RsA


class DRsA(RsA):
    """Class representing an DRsA.    
    """
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def _create_trans_dict(self):
        result = {}
        for t in self.delta:
            key = (frozenset(t.orig.states), frozenset(t.orig.mapping.items()))
            if key not in result:
                result[key] = set()
            result[key].add(t)
        
        #also add states without outgoing transitions
        for q in self.Q:
            key = (frozenset(q.states), frozenset(q.mapping.items()))
            if key not in result:
                result[key] = set()
        return result

    def _update_regs(self, regConf, up, input):
        '''Update Registers.
        Unspecified registers lose their value!'''
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
            
    #TODO: shouldn't be necessary to test regConf.keys()
    def _guard_test_old(self, input, regConf, eqG, diseqG):
        for g in eqG:
            if g in regConf.keys():
                if not input in regConf[g]:
                    return False
        for g in diseqG:
            if g in regConf.keys():
                if input in regConf[g]:
                    return False
        return True
    
    #tests guards of a transition
    def _guard_test(self, input, regConf, eqG, diseqG):
        for g in eqG:
            if not input in regConf[g]:
                return False
                
        for g in diseqG:
            if input in regConf[g]:
                return False
        return True

    def run_word(self, word: str) -> bool:
        '''Runs a word on this drsa'''
        trans_dict = self._create_trans_dict()

        #default reg config
        regConf = {}
        for r in self.R:
            regConf.update({r : set()})
            
        #exactly 1 initial state
        assert len(self.I) == 1
        for i in self.I:
            c = i
        for s in word:
            #print(c.states, str(c.mapping), end='')
            #print('--', end='')
            #print(c.states, s, regConf)

            found = False
            trans_f = None
            for t in trans_dict[(frozenset(c.states),frozenset(c.mapping.items()))]:
                if rsa_is_char_in(s, t.symbol) and self._guard_test(s, regConf, t.eqGuard, t.diseqGuard):
                    if found:
                        # print("FOUND DUPLICATE:")
                        # print(trans_f.orig, trans_f.orig.states, trans_f.orig.mapping, trans_f.symbol, trans_f.eqGuard, trans_f.diseqGuard, trans_f.update)
                        # print(t.orig, t.orig.states, t.orig.mapping, t.symbol, t.eqGuard, t.diseqGuard, t.update)
                        pass
                    found = True
                    trans_f = t
                    #break
            if not found:
                #run dies
                return False
            c = trans_f.dest
            regConf = self._update_regs(regConf,trans_f.update, s)
            #print(c.states)
        for f in self.F:
            if c.states == f.states and c.mapping == f.mapping:
                return True
        else:
            return False
        
    def postprocess(self, oldNRA):
        '''check DRsA overapprox using the postprocessing algorithm'''
        worklist = list()
        Qnew = set()
        Inew = set()
        for q in self.I:
            worklist.append((q, frozenset()))
            Qnew.add((q, frozenset()))
            Inew.add((q, frozenset()))
        Rnew = set()
        deltaNew = set()
        while worklist != list():
            (q, P) = worklist.pop(0)
            for t in self.delta:
                if t.orig.states != q.states or t.orig.mapping != q.mapping :
                    continue
                P1=set()
                up_aux = {}
                up_new = {}
                for r in self.R:
                    Y = set()
                    for y in t.update[r]:
                        if y != IN:
                            for C in P:
                                if y in C:
                                    y = C
                                    break
                        Y.add(y)
                    up_aux[r] = Y
                for Y in up_aux.values():
                    C1 = set()
                    for r in self.R:
                        if up_aux[r] == Y:
                            C1.add(r)
                    P1.add(frozenset(C1))
                    up_new[frozenset(C1)] = Y
                g_eq_new = set()
                g_neq_new = set()
                for C in P:
                    for r in C:
                        if r in t.eqGuard:
                            g_eq_new.add(C)
                        if r in t.diseqGuard:
                            g_neq_new.add(C)
                for C in P1:
                    Rnew.add(C)
                newstate = True
                for q1 in Qnew:
                    if q1[0].states == t.dest.states and\
                       q1[0].mapping == t.dest.mapping and\
                       q1[1] == frozenset(P1):
                        newstate = False
                        break
                if newstate:
                    Qnew.add((t.dest, frozenset(P1)))
                    worklist.append((t.dest, frozenset(P1)))
                deltaNew.add(Transition((q, frozenset(P)), t.symbol, g_eq_new, g_neq_new, up_new, (t.dest, frozenset(P1))))
                
                for q1 in t.dest.states:
                    U = [[]]
                    Rq1 = set()
                    for r in oldNRA._active_regs(q1):
                        Rq1.add(r)
                    #cartesian product
                    for ri in Rq1:
                        Unew = [[]]
                        for elem in U:
                            for rup in up_aux[ri]:
                                tmp = copy.deepcopy(elem)
                                tmp.append([ri, rup])
                                Unew.append(tmp)
                        U = Unew
                    for elem in U:
                        for x in elem:
                            if x[1] == IN:
                                x[1] = frozenset({IN})
                        for t1 in oldNRA.delta:
                            found = True
                            for y in elem:
                                if t1.update[y[0]] not in y[1]:
                                    found = False
                                    break
                            if found:
                                break
                        if not found:
                            return False
        return True

#end of class DRsA



class NRA(RsA):
    """! Class representing an NRA.
    """
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def empty():
        return NRA(set(), set(), set(), set(), set())

    def run_word(self, word):
        raise NotImplementedError

    def complete_updates(self):
        '''fill in implicit updates (r <- r)'''
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

    def fill_with_bottom(self):
        '''fill in implicit bottom updates (r <- _|_)'''
        for t in self.delta:
            for r in self.R:
                if r not in t.update.keys():
                    t.update[r] = BOTTOM

    def make_register_local(self):
        '''convert the NRA to register local form'''
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
        '''run the preprocessing algorithm on the NRA
        (NOT YET COMPATIBLE WITH DETERMINIZE, AS PREPROCESS IS NOT NECESSARY FOR
        REGEX MATCHING)'''
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
                for Cnew in Pnew:
                    found = False
                    tmp = set()
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


    def determinize(self, postprocess=False):
        '''Determinise the NRA into a DRsA'''
        overapprox = False
        #fill in implicit updates
        self.complete_updates()
        self.make_register_local()
        self.fill_with_bottom()
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
            #print(f"({sc.states}, {sc.mapping})")
            #create minterms of all transitions used in a given set of states into A
            #set A includes all symbols used in transitions
            #to avoid looping through the (infinite) alphabet
            sets = set()
            for t in self.delta:
                if t.orig in sc.states:
                    sets.add(t.symbol)
            #print(sets)
            A = _create_minterms(list(sets))
            #print(A)
            regs = set()
            #R[S] \ {r ∈ R | c(r) = 0}:
            for q in sc.states:
                rq = self._active_regs(q)
                for r in rq:
                    if sc.mapping[r] != 0:
                        regs.add(r)
            G = set(powerset(regs))
            for a in A:
                for g in G:
                    g = set(g)
                    T = set()
                    S1 = set()
                    #T ← {q -[a | g=, g!=, ·]-> q′ ∈ ∆ | q ∈ S, g= ⊆ g, g!= ∩ g = ∅}:
                    for t in self.delta:
                        #print(a, t.symbol, myIsSubset(a, t.symbol))
                        if (t.orig in sc.states) and rsa_is_subset(a, t.symbol) and (t.eqGuard.issubset(g))\
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
                    #print(op)
                    #'''
                    #lines 16-19
                    #print("=========", S1, g, "===========")
                    # no need to check if already overapproximating
                    if not overapprox:
                        for q1 in S1:
                            P = [[]]
                            Rq1 = set()
                            for r in self._active_regs(q1):
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
                                    overapprox = True
                                    if not postprocess:
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
                        newA.add_q(s1c1)
                    newA.add_transition(Transition(sc, a, g, self.R.difference(g), up1, s1c1))
        #accepting states:
        for mq in newA.Q:
            for q in mq.states:
                if q in self.F:
                    newA.add_f(mq)
                    break
        if postprocess and overapprox:
            # if postprocess also detects overapprox, abort
            if not newA.postprocess(self):
                return -1
        return newA     
#end of class NRA