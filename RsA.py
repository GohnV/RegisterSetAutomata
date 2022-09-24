#Author: Jan Vašák, 24.9.2022

class Transition:
    orig = ''
    symbol = ''
    eqGuard = {}
    diseqGuard = {}
    update = {}
    dest = ''
    def __init__(self, orig, symbol, eqGuard, diseqGuard, update, dest):
        self.orig = orig
        self.symbol = symbol
        self.eqGuard = eqGuard
        self.diseqGuard = diseqGuard
        self.update = update
        self.dest = dest

class RsA:
    Q = {}          #set of states
    R = {}          #set of registers
    delta = {}      #set of transitions 
    I = {}          #set of initial states
    F = {}          #set of final states

    def __init__(self, Q, R, delta, I, F):
        self.Q = Q
        self.R = R
        self.delta = delta
        self.I = I
        self.F = F

    def runWord(self, word):
        print("This would run", word, "over this RsA")

    """
    #use self.Q.add(...)
        def addQ(self, Q):
            self.Q.add(Q)

        def addR(self, R):
            self.R.add(R)

        def addTransition(self, t):
            self.delta.add(t)

        def addI(self, I):
            self.I.add(I)

        def addF(self, F):
            self.F.add(F)

    """

class DRsA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def runWord(self, word):
        print("This would do a deterministic run of word", word, "on this DRsA")


class NRA(RsA):
    def __init__(self, Q, R, delta, I, F):
        RsA.__init__(self, Q, R, delta, I, F)

    def runWord(self, word):
        print("This would do a nondeterministic run of word", word, "on this NRA")