import RsA as rsa

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


drsa = rsa.DRsA({'q'}, [['r', set()]], set(), {'q'}, {'q'})
drsa.addTransition(rsa.Transition('q','a', set(), {'r'}, [['r','in']],'q'))

word2 = [('a', 'a'), ('a', 'b'), ('a', 'c'), ('a', 'd')]

if drsa.runWord(word2):
    print("Accepted")
else:
    print("Rejected")