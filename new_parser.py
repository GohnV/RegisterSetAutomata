import sre_parse as p
import sre_constants as c
import pprint
import rsa_draw
from RsA import *

# TODO: Figure out capture, backref
# TODO: TEST (probably start with unit testing automata functions)

g_state_id = 0

def get_new_state_id() -> int:
    global g_state_id
    tmp = g_state_id
    g_state_id += 1
    return tmp
    

subexp = p.parse('[^a-zX]te(s*)(?:t|.* | x | as-x)+\\1')
subexp = p.parse('a{3,5}(a|b|cd)xyz')

def concatenate_aut(first: NRA, second: NRA) -> NRA:
    new_aut = NRA.empty()
    new_aut.importAutomaton(first)
    new_aut.importAutomaton(second)

    #add connecting transitions
    #from every final state of first
    #to every initial state of second
    for f in first.F:
        for i in second.I:
            new_aut.addTransition(Transition(f,EPSILON,set(),set(),{},i))

    new_aut.I = {i for i in first.I}
    new_aut.F = {f for f in second.F}
    return new_aut


def one_trans_aut(chars:set, negate: bool = False) -> NRA:
    if negate:
        symbol = ('^', frozenset(chars))
    else:
        symbol = (' ', frozenset(chars))
    q1 = get_new_state_id()
    q2 = get_new_state_id()
    t = Transition(q1, symbol, set(), set(), {}, q2)
    return NRA({q1, q2}, set(), {t}, {q1}, {q2})

#copy automaton while making sure state ids are kept unique
def copy_aut(aut: NRA) -> NRA:
    state_dict = {}
    for q in aut.Q:
        state_dict[q] = get_new_state_id()
    ret_aut = NRA.empty()
    ret_aut.Q = state_dict.values()
    ret_aut.I = {state_dict[i] for i in aut.I}
    ret_aut.F = {state_dict[f] for f in aut.F}
    ret_aut.R = aut.R
    for t in aut.delta:
        t_new = Transition(state_dict[t.orig], t.symbol, t.eqGuard, t.diseqGuard, t.update, state_dict[t.dest])
        ret_aut.addTransition(t_new)
    return ret_aut

def iterate_aut(aut:NRA) -> NRA:
    ret_aut = NRA.empty()
    ret_aut.importAutomaton(aut)
    #add transition from every final state to every initial state
    for f in aut.F:
        for i in aut.I:
            t = Transition(f, EPSILON, set(), set(), {}, i)
            aut.addTransition(t)
    #make initial states final
    ret_aut.I = {i for i in aut.I}
    ret_aut.F = aut.F.union(aut.I)
    return aut

def repeat_aut(aut: NRA, min: int, max) -> NRA:
    init_state = get_new_state_id()
    #only accept empty string
    ret_aut = NRA({init_state}, set(), set(), {init_state}, {init_state})

    for i in range(min):
        tmp = copy_aut(aut)
        ret_aut = concatenate_aut(ret_aut, tmp)
    if (max is c.MAXREPEAT):
        tmp = iterate_aut(aut)
        ret_aut = concatenate_aut(ret_aut, tmp)
    else:
    #CHECK OFF BY ONE ERRORS
        tmp_states = {f for f in ret_aut.F} #we dont need more repetitions to accept
        for i in range(max-min):
            tmp = copy_aut(aut)
            tmp_states = tmp_states.union(tmp.F)
            ret_aut = concatenate_aut(ret_aut, tmp)
            ret_aut.F = ret_aut.F.union(tmp.F)
        ret_aut.F = ret_aut.F.union(tmp_states)
    return ret_aut

def branch_aut(auts: set) -> NRA:
    init_state = get_new_state_id()
    fin_state = get_new_state_id()
    #only accept empty string initially
    ret_aut = NRA({init_state, fin_state}, set(), set(), {init_state}, {fin_state})
    for a in auts:
        ret_aut.importAutomaton(a)
        for i in a.I:
            t = Transition(init_state, EPSILON, set(), set(), {}, i)
            ret_aut.addTransition(t)
        for f in a.F:
            t = Transition(f, EPSILON, set(), set(), {}, fin_state)
            ret_aut.addTransition(t)
    return ret_aut

def create_automaton(sub_exp, level=0):
    #nl = True
    #seqtypes = (tuple, list)
    init_state = get_new_state_id()
    #only accept empty string initially
    ret_automaton = NRA({init_state}, set(), set(), {init_state}, {init_state})
    aut_tmp = NRA.empty()
    #CONCATENATE ALL AUTOMATA CREATED IN THIS LOOP
    for op, av in sub_exp.data:
        print(level*"  " + str(op), end='')
        if op is c.IN:
            # member sublanguage
            print()
            neg = False
            chars = set()
            if av[0] == (c.NEGATE, None):
                print(c.NEGATE)
                neg = True
                av.pop(0)
            for op, a in av:
                if op == c.RANGE:
                   start, end = a
                   for i in range(start, end):
                       chars.add(chr(i))  
                elif op == c.LITERAL:
                    chars.add(chr(a))
                print((level+1)*"  " + str(op), a)
            #CREATE_AUT
            aut_tmp = one_trans_aut(chars, negate=neg)
        elif op is c.BRANCH:
            print()
            #BRANCH ALL AUTOMATA CREATED IN THE LOOP
            branch_auts = set()
            for i, a in enumerate(av[1]):
                if i:
                    print(level*"  " + "OR")
                #a.dump(level+1)
                branch_auts.add(create_automaton(a, level+1))
            aut_tmp = branch_aut(branch_auts)

        elif op is c.GROUPREF_EXISTS:
            #IDK WHAT THIS MEANS
            condgroup, item_yes, item_no = av
            print('', condgroup)
            item_yes.dump(level+1)
            if item_no:
                print(level*"  " + "ELSE")
                item_no.dump(level+1)

        # elif isinstance(av, seqtypes):
        #     #CHECK FOR MAX_REPEAT/MIN_REPEAT SOMEWHERE HERE
        #     nl = False
        #     for a in av:
        #         if isinstance(a, p.SubPattern):
        #             #print("test")
        #             #CAPTURE GROUP
        #             if not nl:
        #                 print()
        #             #a.dump(level+1)
        #             create_automaton(a, level+1)
        #             nl = True
        #         else:
        #             if not nl:
        #                 print(' ', end='')
        #             print(a, end='')
        #             nl = False
        #     if not nl:
        #         print()
        
        elif op is c.SUBPATTERN:
            #CAPTURE GROUP
            group_num = av[0]
            idk1 = av[1] # TODO: CHECK MEANING
            idk2 = av[2] # TODO: CHECK MEANING
            sub_pattern = av[3]
            print(" ", end='')
            print(group_num, idk1, idk2)
            aut_tmp = create_automaton(sub_pattern, level+1) 

        elif op is c.MAX_REPEAT or op is c.MIN_REPEAT:
            min = av[0]
            max = av[1]
            sub_pattern = av[2]
            print(" ", end='')
            print(min,max)
            aut_tmp = create_automaton(sub_pattern, level+1)
            aut_tmp = repeat_aut(aut_tmp, min, max)

        elif op is c.LITERAL:
            print('', av)
            #CREATE_AUT:
            aut_tmp = one_trans_aut({chr(av)})

        #FIXME: HANDLE ANYCHAR (and others???)
        else:
            #can be backref
            print('', av)

        #end of elif chain
        ret_automaton = concatenate_aut(ret_automaton, aut_tmp)
    #end of for loop
    return ret_automaton

subexp_aut = create_automaton(subexp)
rsa_draw.drawAutomaton(subexp_aut, "testaut")