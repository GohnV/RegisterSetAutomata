#Author: Jan Vašák, 24.9.2022




class Transition:
    orig = ''
    symbol = ''
    eqGuard = set()
    diseqGuard = set()
    update = set()      #{('r1', 5), ...}
    dest = ''
    def __init__(self, orig, symbol, eqGuard, diseqGuard, update, dest):
        self.orig = orig
        self.symbol = symbol
        self.eqGuard = eqGuard
        self.diseqGuard = diseqGuard
        self.update = update
        self.dest = dest

class RsA:
    Q = set()          #set of states
    R = list()             #list(python doesn't have nested sets?) of registers {([r1', {5, 4, 1}], ...}
    delta = set()      #set of transitions 
    I = set()          #set of initial states
    F = set()          #set of final states

    def __init__(self, Q, R, delta, I, F):
        self.Q = Q
        self.R = R
        self.delta = delta
        self.I = I
        self.F = F

    #up shouldn't update the same register multiple times with different values
    def updateRegs(self, up, input):
        for val in up:
            for r in self.R: 
                if r[0] == val[0]:
                    if val[1] == 'in':
                        r[1].add(input)
                    else:
                        r[1].add(val[1])

    def clearRegs(self):
        for r in self.R:
            r[1] = set()

    def guardTest(self, val, eqG, diseqG):
        #(self.guardTest(i[1], t.eqGuard) or t.eqGuard == set()) and (t.diseqGuard == set() or not self.guardTest(i[1], t.diseqGuard))
        #is there a register in the guard that does not have in (val) as it's element?
        for g in eqG:
            for r in self.R:
                if g == r[0]:
                    if not {val}.issubset(r[1]):
                        return False

        for g in diseqG:
            for r in self.R:
                if g == r[0]:
                    if {val}.issubset(r[1]):
                        return False
        return True

    def runWord(self, word):
        print("This would run", word, "over this RsA")

#Revisit these
    def addQ(self, Q):
        self.Q.add(Q)

    def addR(self, reg):
        self.R.append(reg)

    def addTransition(self, t):
        self.delta.add(t)

    def addI(self, I):
        self.I.add(I)

    def addF(self, F):
        self.F.add(F)

class DRsA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def runWord(self, word):
        cnt = 0
        c = ''
        for i in self.I:
            c = i
            cnt += 1
        if cnt > 1:
            print("Multiple initial states in a deterministic automaton! Unspecified behavior.")
        for i in word:
            cnt = 0
            for t in self.delta:
                if t.orig == c and t.symbol == i[0] and self.guardTest(i[1], t.eqGuard, t.diseqGuard):
                    #assuming there is only one such transition
                    c = t.dest
                    self.updateRegs(t.update, i[1])
                    cnt += 1 
                    break
            if cnt == 0:
                #no possible transition, run dies
                self.clearRegs()
                return False
        if {c}.issubset(self.F):
            self.clearRegs()
            return True
        else:
            self.clearRegs()
            return False
                        


class NRA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def runWord(self, word):
        print("This would do a nondeterministic run of word", word, "on this NRA")