import sre_parse as p
import sre_constants as c
import pprint
import rsa_draw
from RsA import *

# TODO: Add backref, capt group to create_automaton and test!!!

g_state_id = 0 # for generating sequential ids for states
g_back_referenced = [] # store all back-referenced capture group numbers
g_anchor_start = False
g_anchor_end = False
g_simulate_transducer = False

def get_new_state_id() -> int:
    global g_state_id
    tmp = g_state_id
    g_state_id += 1
    return tmp

def reg_of_num(capt_num: int) -> str:
    return "r"+str(capt_num)

def find_br_cg(sub_pattern: p.SubPattern): #Ifs taken from SubPattern.dump()
    global g_back_referenced
    seqtypes = (tuple, list)
    for op, av in sub_pattern.data:
        if op is c.BRANCH:
            for a in av[1]:
                find_br_cg(a)
        elif op is c.GROUPREF_EXISTS:
            condgroup, item_yes, item_no = av
            find_br_cg(item_yes)
            if item_no:
                find_br_cg(item_no)
        elif isinstance(av, seqtypes):
            for a in av:
                if isinstance(a, p.SubPattern):
                    find_br_cg(a)
        elif op is c.GROUPREF:
            g_back_referenced.append(av)

def unachnor_aut(aut: NRA) -> NRA:
    new_aut = NRA.empty()
    new_aut.importAutomaton(aut)
    start_state = get_new_state_id()
    end_state = get_new_state_id()
    new_aut.addQ(start_state)
    new_aut.addQ(end_state)
    new_aut.addI(start_state)
    new_aut.addF(end_state)
    if not g_anchor_start:
        t = Transition(start_state, ANYCHAR, set(), set(), {}, start_state)
        new_aut.addTransition(t)
    if not g_anchor_end:
        t = Transition(end_state, ANYCHAR, set(), set(), {}, end_state)
        new_aut.addTransition(t)
    for i in aut.I:
        t = Transition(start_state, EPSILON, set(), set(), {}, i)
        new_aut.addTransition(t)
    for f in aut.F:
        t = Transition(f, EPSILON, set(), set(), {}, end_state)
        new_aut.addTransition(t)
    return new_aut

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

def check_fix_len(sub_pattern: p.SubPattern) -> (int, tuple) or False:
    length = 0
    chars = (' ', set())
    for op, av in sub_pattern.data:
        #print(op, av)
        if op is c.BRANCH:
            lens = []
            #Check if length of all branches is equal
            for b in av[1]:
                b_ret = check_fix_len(b)
                if b_ret == False: #checking equality to false to prevent potential empty tuple shenanigans
                    return False
                b_len, b_chars = b_ret
                lens.append(b_len)
                chars = myUnion(chars, b_chars)
            assert(len(lens) > 0)
            check_len = -1
            for i in lens:
                if check_len == -1:
                    check_len = i
                elif check_len != i:
                    return False
            length += check_len

        elif op is c.MAX_REPEAT or op is c.MIN_REPEAT:
            #check if max and min are the same
            rep_min, rep_max, rep_pat = av
            if rep_min != rep_max:
                return False
            rep_ret = check_fix_len(rep_pat)
            if rep_ret == False: #checking equality to false to prevent potential empty tuple shenanigans
                return False
            rep_chars, rep_len = rep_ret
            length += rep_len
            chars = myUnion(chars, rep_chars)

        elif op is c.LITERAL:
            length += 1
            myAddChar(chars, chr(av))

        elif op is c.ANY:
            length += 1
            chars = ANYCHAR

        elif op is c.IN:
            length += 1
            neg_sign = ' '
            if av[0] == c.NEGATE:
                neg_sign = '^'
                av_chars = av[1:]
            else:
                av_chars = av
            in_char_set = (neg_sign, set())
            for a in av_chars: 

                a_op, a_av = a
                if a_op is c.RANGE:
                    start, end = a_av
                    for i in range(start, end):
                        myAddChar(in_char_set, chr(i))  
                elif a_op is c.LITERAL:
                    myAddChar(in_char_set, chr(a_av))
            chars = myUnion(chars, in_char_set)
        elif op is c.NOT_LITERAL:
            length += 1
            chars = myUnion(chars, ('^', {chr(av)}))
        #end elif chain
        else:
            # unsupported construction
            return False
    #end for loop
    #freeze set:
    chars = (chars[0], frozenset(chars[1]))
    #print("length", length, "chars", chars)
    return length, chars

# check if capture group is static length and
# create an automaton with all the possible characters
def capt_group_aut(sub_pattern: p.SubPattern, capt_num: int) -> NRA: 
    ret = check_fix_len(sub_pattern)
    if ret == False: #checking equality to False to prevent potential empty tuple shenanigans
        return False
    len, symb = ret
    if ((not g_simulate_transducer) and len > 1):
        return False
    #create automaton
    q1 = get_new_state_id()
    q2 = get_new_state_id()
    r = reg_of_num(capt_num)
    t = Transition(q1, symb, set(), set(), {r : IN}, q2)
    return NRA({q1, q2}, {r}, {t}, {q1}, {q2})

def backref_aut(capt_num: int) -> NRA:
    q1 = get_new_state_id()
    q2 = get_new_state_id()
    r = reg_of_num(capt_num)
    t = Transition(q1, ANYCHAR, {r}, set(), {}, q2)
    return NRA({q1, q2}, {r}, {t}, {q1}, {q2})

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
            ret_aut.addTransition(t)
    #make initial states final
    ret_aut.I = {i for i in aut.I}
    ret_aut.F = aut.F.union(aut.I)
    return ret_aut

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
    global g_anchor_start, g_anchor_end
    #nl = True
    #seqtypes = (tuple, list)
    init_state = get_new_state_id()
    #only accept empty string initially
    ret_automaton = NRA({init_state}, set(), set(), {init_state}, {init_state})
    aut_tmp = NRA.empty()
    #CONCATENATE ALL AUTOMATA CREATED IN THIS LOOP
    for op, av in sub_exp.data:
        #print(level*"  " + str(op), end='')
        if op is c.IN:
            # member sublanguage
            #print()
            neg = False
            chars = set()
            if av[0] == (c.NEGATE, None):
                #print(c.NEGATE)
                neg = True
                av.pop(0)
            for op, a in av:
                if op == c.RANGE:
                   start, end = a
                   for i in range(start, end):
                       chars.add(chr(i))  
                elif op == c.LITERAL:
                    chars.add(chr(a))
                #print((level+1)*"  " + str(op), a)
            #CREATE_AUT
            aut_tmp = one_trans_aut(chars, negate=neg)
        elif op is c.BRANCH:
            #print()
            #BRANCH ALL AUTOMATA CREATED IN THE LOOP
            branch_auts = set()
            for i, a in enumerate(av[1]):
                if i:
                    #print(level*"  " + "OR")
                    pass
                #a.dump(level+1)
                branch_auts.add(create_automaton(a, level+1))
            aut_tmp = branch_aut(branch_auts)

        elif op is c.GROUPREF_EXISTS:
            # TODO: IDK WHAT THIS MEANS
            condgroup, item_yes, item_no = av
            #print('CONDGROUP', op, condgroup)
            #item_yes.dump(level+1)
            if item_no:
                #print(level*"  " + "ELSE")
                #item_no.dump(level+1)
                pass
            return False #not supported yet
        
        elif op is c.SUBPATTERN:
            #CAPTURE GROUP
            group_num = av[0]
            idk1 = av[1] # TODO: CHECK MEANING
            idk2 = av[2] # TODO: CHECK MEANING
            sub_pattern = av[3]
            #print(" ", end='')
            #print(group_num, idk1, idk2)
            # if backreferenced, call create_capture or whatever its called, else call create_automaton
            if group_num in g_back_referenced:
                aut_tmp = capt_group_aut(sub_pattern, group_num)
            else:
                aut_tmp = create_automaton(sub_pattern, level+1) 

        elif op is c.MAX_REPEAT or op is c.MIN_REPEAT:
            min = av[0]
            max = av[1]
            sub_pattern = av[2]
            #print(" ", end='')
            #print(min,max)
            aut_tmp = create_automaton(sub_pattern, level+1)
            aut_tmp = repeat_aut(aut_tmp, min, max)

        elif op is c.LITERAL:
            #print('', av)
            #CREATE_AUT:
            aut_tmp = one_trans_aut({chr(av)})

        elif op is c.NOT_LITERAL:
            #print('', av)
            #CREATE_AUT:
            aut_tmp = one_trans_aut({chr(av)}, negate=True)

        elif op is c.ANY:
            #print('', av)
            aut_tmp = one_trans_aut(set(), negate=True) #create anychar

        elif op is c.GROUPREF:
            #print('', av)
            aut_tmp = backref_aut(av)

        elif op is c.AT:
            if av is c.AT_BEGINNING:
                g_anchor_start = True
                continue #dont concatenate
            elif av is c.AT_END:
                g_anchor_end = True
                continue #dont concatenate
            else:
                return False

        else:
            
            # UNSUPPORTED: (TODO: which should be supported?)
            #       ASSERT
            #       ASSERT_NOT
            #       AT_BEGINNING_STRING
            #       AT_BOUNDARY

            #print('IN ELSE', op, av)
            return False #not supported

        #end of elif chain
        if aut_tmp == False:
            return False
        ret_automaton = concatenate_aut(ret_automaton, aut_tmp)   
    #end of for loop
    return ret_automaton


##################################################################################
#                                API DEFINITION?                                 #
##################################################################################

def attempt_rsa(pattern: str) -> bool:
    global g_back_referenced, g_anchor_start, g_anchor_end
    g_back_referenced = []
    g_anchor_start = False
    g_anchor_end = False
    pat = p.parse(pattern)
    find_br_cg(pat)
    nra = create_automaton(pat)
    if nra == False:
        return False
    #print(nra)
    nra = unachnor_aut(nra)
    nra.removeEps()
    nra.removeUnreachable()
    rsa = nra.determinize()
    #print(rsa)
    return rsa != -1

def create_nra(pattern: str):
    global g_back_referenced, g_anchor_start, g_anchor_end
    g_back_referenced = []
    g_anchor_start = False
    g_anchor_end = False
    pat = p.parse(pattern)
    find_br_cg(pat)
    nra = create_automaton(pat)
    nra = unachnor_aut(nra)
    return nra

def create_rsa(pattern: str) -> DRsA or bool:
    global g_back_referenced, g_anchor_start, g_anchor_end
    g_back_referenced = []
    g_anchor_start = False
    g_anchor_end = False
    pat = p.parse(pattern)
    find_br_cg(pat)
    nra = create_automaton(pat)
    if nra == False:
        return False
    #print(nra)
    nra = unachnor_aut(nra)
    nra.removeEps()
    nra.removeUnreachable()
    rsa = nra.determinize()
    #print(rsa)
    if rsa == -1:
        return False
    else:
        return rsa

##################################################################################
#                                TESTING AREA                                    #
##################################################################################
# subexp = p.parse('[^a-zX]te(s*)(?:t|.* | x | as-x)+\\1')
# subexp = p.parse('.*a{3,5}(x(?:ab|bc|dc))xyz\\1')

#FIXME: test this ((.). \2.) (.*)((.). \5. \5.)



# pattern = '.[^b]a{3,5}(x(?:ab|bc|dc))xyz\\1$'
# g_back_referenced = []
# g_anchor_start = False
# g_anchor_end = False
# pat = p.parse(pattern)
# find_br_cg(pat)
# nra = create_automaton(pat)
# if nra == False:
#     print("error")
#     exit()
# nra = unachnor_aut(nra)
# nra.removeEps()
# nra.removeUnreachable()
# rsa_draw.drawAutomaton(nra, "testaut")
# rsa = nra.determinize()
# if rsa == -1:
#     print("unable to determinize")
#     exit()
# rsa_draw.drawAutomaton(rsa, "testaut_det")

# import time

# while True:
#     word = input()
#     print("\n", word, " is ", sep='', end="")
#     t0 = time.time()
#     res = rsa.runWord(word)
    
#     if res:
#         print("accepted")
#     else:
#         print("not accepted")
#     t1 = time.time()
#     print("time:", t1-t0)
