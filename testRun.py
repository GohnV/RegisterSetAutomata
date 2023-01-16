import RsA as rsa
import rsa_utils as ru
import rsa_draw as rd
import time
#file to play with whatever I just finished to check basic functionality



#@-capture character
#&-concatenation
#numbers are backreferences
#regex = ".*&@&.*&@&.*&2&.*&1&.*$"
#regex = ".*&@&@&.*&;&.*&2&1&.*$"
#regex = ".*&@&.*&;&.*&@&.*&;&.*&1&2$"
#        ^.*(.).* ; .*(.).* ; .*\1\2$

#regex = ".*&@&.*&1&;&1&1&.*&;&.*&1$"
#       ^.*(.).*\1 ;\1\1 .* ; .*\1$

#regex = ".*&@&.*&;&1&;&1&.*&;&.*&1$"
#       ^.*(.).* ;\1 ;\1 .* ; .*\1$      
    
#regex = "@&.*&;&.*&1$"
#      ^(.).* ; .*\1$
# vypada bez problemu
    
#regex = ".*&@&;&.*&1$"
#       ^.*(.); .*\1$
# nefunguje pro a;;;a

#zaludne:
regex = ".*&@&.*&1&;&.*&;&.*&1$"
#       ^.*(.).*\1 ; .* ; .*\1$

regex = ".*&@&.*&1&;&1&1&.*&;&.*&1$"     
#       ^.*(.).*\1 ;\1\1 .* ; .*\1$

regex = ".*&@&.*&1&.*&;&.*&;&.*&1$"
#       ^.*(.).*\1 .* ; .* ; .*\1$

regex = "[test]$"

#regex = "@&.*&;&.*&@&.*&;&.*&@&.*&3&2&1$"
#parsedTree = createTree('')
#parsedTree = createTree(".*&a&b&c&.*$")
#parsedTree = createTree(".*&@&.*&1&.*$")
#parsedTree = createTree("@&a&b&c&1$")
#parsedTree = createTree('.*&@&.*&;&.*&@&.*&;&2&1$')
#parsedTree = createTree(".*&@&.*&1&.*$")    
parsedTree = ru.createTree(regex)
rd.drawSyntaxTree(parsedTree, "parsedTree")
id = rsa.Counter()
parsedTree.createAutomaton(id)
parsedAutomaton = parsedTree.automaton
parsedAutomaton.joinStates()
parsedAutomaton.removeEps()
parsedAutomaton.removeUnreachable()

rd.drawAutomaton(parsedAutomaton, "parsedAutomaton") 

print("my_regex: ", regex)
print("\nNRA\n------")
print("states: ", len(parsedAutomaton.Q))
print("transitions: ", len(parsedAutomaton.delta))
print("registers: ", len(parsedAutomaton.R))


detAut = parsedAutomaton.determinize()
#drawAutomaton(detAut, "detAutomaton")

if detAut == -1:
    print("Unable to determinize")
    exit()

print("\nDRsA\n------")
print("states: ", len(detAut.Q))
print("transitions: ", len(detAut.delta))
print("registers: ", len(detAut.R))

while True:
    word = input()
    print("\n", word, " is ", sep='', end="")
    t0 = time.time()
    res = detAut.runWord(word)
    
    if res:
        print("accepted")
    else:
        print("not accepted")
    t1 = time.time()
    print("time:", t1-t0)



'''
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