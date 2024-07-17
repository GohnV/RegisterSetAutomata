import sre_parse as p
import sre_constants as c
from rsaregex.RsAtools import *
from typing import Union

WHITESPACE = frozenset(" \t\n\r\v\f")
DIGITS = frozenset("0123456789")
ASCIILETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
#TODO: no unicode for word yet
WORD_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

g_state_id = 0 # for generating sequential ids for states
g_back_referenced = [] # store all back-referenced capture group numbers
g_anchor_start = False
g_anchor_end = False
g_simulate_transducer = False

def _get_new_state_id() -> int:
    global g_state_id
    tmp = g_state_id
    g_state_id += 1
    return tmp

def _reg_of_num(capt_num: int) -> str:
    return "r"+str(capt_num)

def _find_br_cg(sub_pattern: p.SubPattern):
    global g_back_referenced
    seqtypes = (tuple, list)
    for op, av in sub_pattern.data:
        if op is c.BRANCH:
            for a in av[1]:
                _find_br_cg(a)
        elif op is c.GROUPREF_EXISTS:
            condgroup, item_yes, item_no = av
            _find_br_cg(item_yes)
            if item_no:
                _find_br_cg(item_no)
        elif isinstance(av, seqtypes):
            for a in av:
                if isinstance(a, p.SubPattern):
                    _find_br_cg(a)
        elif op is c.GROUPREF:
            g_back_referenced.append(av)

def _unanchor_aut(aut: NRA) -> NRA:
    new_aut = NRA.empty()
    new_aut.import_automaton(aut)
    start_state = _get_new_state_id()
    end_state = _get_new_state_id()
    new_aut.add_q(start_state)
    new_aut.add_q(end_state)
    new_aut.add_i(start_state)
    new_aut.add_f(end_state)
    if not g_anchor_start:
        t = Transition(start_state, ANYCHAR, set(), set(), {}, start_state)
        new_aut.add_transition(t)
    if not g_anchor_end:
        t = Transition(end_state, ANYCHAR, set(), set(), {}, end_state)
        new_aut.add_transition(t)
    for i in aut.I:
        t = Transition(start_state, EPSILON, set(), set(), {}, i)
        new_aut.add_transition(t)
    for f in aut.F:
        t = Transition(f, EPSILON, set(), set(), {}, end_state)
        new_aut.add_transition(t)
    return new_aut

def _concatenate_aut(first: NRA, second: NRA) -> NRA:
    new_aut = NRA.empty()
    new_aut.import_automaton(first)
    new_aut.import_automaton(second)

    #add connecting transitions
    #from every final state of first
    #to every initial state of second
    for f in first.F:
        for i in second.I:
            new_aut.add_transition(Transition(f,EPSILON,set(),set(),{},i))

    new_aut.I = {i for i in first.I}
    new_aut.F = {f for f in second.F}
    return new_aut

def _one_trans_aut(chars:set, negate: bool = False) -> NRA:
    if negate:
        symbol = ('^', frozenset(chars))
    else:
        symbol = (' ', frozenset(chars))
    q1 = _get_new_state_id()
    q2 = _get_new_state_id()
    t = Transition(q1, symbol, set(), set(), {}, q2)
    return NRA({q1, q2}, set(), {t}, {q1}, {q2})

def _check_fix_len(sub_pattern: p.SubPattern) -> (int, tuple) or False:
    length = 0
    chars = (' ', set())
    for op, av in sub_pattern.data:
        #print(op, av)
        if op is c.BRANCH:
            lens = []
            #Check if length of all branches is equal
            for b in av[1]:
                b_ret = _check_fix_len(b)
                if b_ret == False: #checking equality to false to prevent potential empty tuple shenanigans
                    return False
                b_len, b_chars = b_ret
                lens.append(b_len)
                chars = rsa_set_union(chars, b_chars)
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
            rep_ret = _check_fix_len(rep_pat)
            if rep_ret == False: #checking equality to false to prevent potential empty tuple shenanigans
                return False
            rep_chars, rep_len = rep_ret
            length += rep_len
            chars = rsa_set_union(chars, rep_chars)

        elif op is c.LITERAL:
            length += 1
            rsa_set_add_char(chars, chr(av))

        elif op is c.ANY:
            length += 1
            chars = ANYCHAR

        elif op is c.IN:
            length += 1
            neg_sign = ' '
            if av[0][0] == c.NEGATE:
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
                        in_char_set[1].add(chr(a_av))
                elif a_op is c.LITERAL:
                    in_char_set[1].add(chr(a_av))
            chars = rsa_set_union(chars, in_char_set)
        elif op is c.NOT_LITERAL:
            length += 1
            chars = rsa_set_union(chars, ('^', {chr(av)}))
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
def _capt_group_aut(sub_pattern: p.SubPattern, capt_num: int) -> NRA: 
    ret = _check_fix_len(sub_pattern)
    if ret == False: #checking equality to False to prevent potential empty tuple shenanigans
        return False
    len, symb = ret
    if ((not g_simulate_transducer) and len > 1):
        return False
    #create automaton
    q1 = _get_new_state_id()
    q2 = _get_new_state_id()
    r = _reg_of_num(capt_num)
    t = Transition(q1, symb, set(), set(), {r : IN}, q2)
    return NRA({q1, q2}, {r}, {t}, {q1}, {q2})

def _backref_aut(capt_num: int) -> NRA:
    q1 = _get_new_state_id()
    q2 = _get_new_state_id()
    r = _reg_of_num(capt_num)
    t = Transition(q1, ANYCHAR, {r}, set(), {}, q2)
    return NRA({q1, q2}, {r}, {t}, {q1}, {q2})

#copy automaton while making sure state ids are kept unique
def _copy_aut(aut: NRA) -> NRA:
    state_dict = {}
    for q in aut.Q:
        state_dict[q] = _get_new_state_id()
    ret_aut = NRA.empty()
    ret_aut.Q = state_dict.values()
    ret_aut.I = {state_dict[i] for i in aut.I}
    ret_aut.F = {state_dict[f] for f in aut.F}
    ret_aut.R = aut.R
    for t in aut.delta:
        t_new = Transition(state_dict[t.orig], t.symbol, t.eqGuard, t.diseqGuard, t.update, state_dict[t.dest])
        ret_aut.add_transition(t_new)
    return ret_aut

def _iterate_aut(aut:NRA) -> NRA:
    ret_aut = NRA.empty()
    ret_aut.import_automaton(aut)
    #add transition from every final state to every initial state
    for f in aut.F:
        for i in aut.I:
            t = Transition(f, EPSILON, set(), set(), {}, i)
            ret_aut.add_transition(t)
    #make initial states final
    ret_aut.I = {i for i in aut.I}
    ret_aut.F = aut.F.union(aut.I)
    return ret_aut

def _repeat_aut(aut: NRA, min: int, max) -> NRA:
    init_state = _get_new_state_id()
    #only accept empty string
    ret_aut = NRA({init_state}, set(), set(), {init_state}, {init_state})

    for i in range(min):
        tmp = _copy_aut(aut)
        ret_aut = _concatenate_aut(ret_aut, tmp)
    if (max is c.MAXREPEAT):
        tmp = _iterate_aut(aut)
        ret_aut = _concatenate_aut(ret_aut, tmp)
    else:
    #CHECK OFF BY ONE ERRORS
        tmp_states = {f for f in ret_aut.F} #we dont need more repetitions to accept
        for i in range(max-min):
            tmp = _copy_aut(aut)
            tmp_states = tmp_states.union(tmp.F)
            ret_aut = _concatenate_aut(ret_aut, tmp) 
            ret_aut.F = ret_aut.F.union(tmp.F)
        ret_aut.F = ret_aut.F.union(tmp_states)
    return ret_aut

def _branch_aut(auts: set) -> NRA:
    init_state = _get_new_state_id()
    fin_state = _get_new_state_id()
    #only accept empty string initially
    ret_aut = NRA({init_state, fin_state}, set(), set(), {init_state}, {fin_state})
    for a in auts:
        ret_aut.import_automaton(a)
        for i in a.I:
            t = Transition(init_state, EPSILON, set(), set(), {}, i)
            ret_aut.add_transition(t)
        for f in a.F:
            t = Transition(f, EPSILON, set(), set(), {}, fin_state)
            ret_aut.add_transition(t)
    return ret_aut

def _create_automaton(sub_exp, level=0):
    global g_anchor_start, g_anchor_end
    #nl = True
    #seqtypes = (tuple, list)
    init_state = _get_new_state_id()
    #only accept empty string initially
    ret_automaton = NRA({init_state}, set(), set(), {init_state}, {init_state})
    aut_tmp = NRA.empty()
    #CONCATENATE ALL AUTOMATA CREATED IN THIS LOOP
    for op, av in sub_exp.data:
        #print(level*"  " + str(op), end='')
        if op is c.IN:
            # member sublanguage
            #print()
            neg = ' '
            chars = set()
            if av[0] == (c.NEGATE, None):
                #print(c.NEGATE)
                neg = '^'
                av.pop(0)
            for op, a in av:
                
                if op == c.RANGE:
                   start, end = a
                   for i in range(start, end):
                       chars.add(chr(i))  
                elif op == c.LITERAL:
                    chars.add(chr(a))
                elif op == c.CATEGORY:
                    myset_chars = (neg, frozenset(chars))
                    if a == c.CATEGORY_SPACE:
                        neg, chars = rsa_set_union(myset_chars, (' ', WHITESPACE))
                    elif a == c.CATEGORY_NOT_SPACE:
                        neg, chars = rsa_set_union(myset_chars, ('^', WHITESPACE))
                    elif a == c.CATEGORY_DIGIT:
                        neg, chars = rsa_set_union(myset_chars, (' ', DIGITS))
                    elif a == c.CATEGORY_NOT_DIGIT:
                        neg, chars = rsa_set_union(myset_chars, ('^', DIGITS))
                    elif a == c.CATEGORY_WORD:
                        neg, chars = rsa_set_union(myset_chars, (' ', WORD_CHARS))
                    elif a == c.CATEGORY_NOT_WORD:
                        neg, chars = rsa_set_union(myset_chars, ('^', WORD_CHARS))
                    else:
                        print(op, a)
                        return False #unsupported category
                    chars = set(chars)
                else:
                    print(op, a)
                    return False #unsupported type
                #print((level+1)*"  " + str(op), a)
            #CREATE_AUT
            aut_tmp = _one_trans_aut(chars, negate=(neg == '^'))
        elif op is c.BRANCH:
            #print()
            #BRANCH ALL AUTOMATA CREATED IN THE LOOP
            _branch_auts = set()
            for i, a in enumerate(av[1]):
                if i:
                    #print(level*"  " + "OR")
                    pass
                #a.dump(level+1)
                _branch_auts.add(_create_automaton(a, level+1))
            aut_tmp = _branch_aut(_branch_auts)

        elif op is c.GROUPREF_EXISTS:
            return False #TODO: not supported yet
        
        elif op is c.SUBPATTERN:
            #CAPTURE GROUP
            group_num = av[0]
            sub_pattern = av[3]
            #print(" ", end='')
            # if backreferenced, call create_capture or whatever its called, else call _create_automaton
            if group_num in g_back_referenced:
                aut_tmp = _capt_group_aut(sub_pattern, group_num)
            else:
                aut_tmp = _create_automaton(sub_pattern, level+1) 

        elif op is c.MAX_REPEAT or op is c.MIN_REPEAT:
            min = av[0]
            max = av[1]
            sub_pattern = av[2]
            #print(" ", end='')
            #print(min,max)
            aut_tmp = _create_automaton(sub_pattern, level+1)
            aut_tmp = _repeat_aut(aut_tmp, min, max)

        elif op is c.LITERAL:
            #print('', av)
            #CREATE_AUT:
            aut_tmp = _one_trans_aut({chr(av)})

        elif op is c.NOT_LITERAL:
            #print('', av)
            #CREATE_AUT:
            aut_tmp = _one_trans_aut({chr(av)}, negate=True)

        elif op is c.ANY:
            #print('', av)
            aut_tmp = _one_trans_aut(set(), negate=True) #create anychar

        elif op is c.GROUPREF:
            #print('', av)
            aut_tmp = _backref_aut(av)

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
        ret_automaton = _concatenate_aut(ret_automaton, aut_tmp)   
    #end of for loop
    return ret_automaton




def create_nra(pattern: str) -> Union[NRA, bool]:
    global g_back_referenced, g_anchor_start, g_anchor_end
    g_back_referenced = []
    g_anchor_start = False
    g_anchor_end = False
    pat = p.parse(pattern)
    _find_br_cg(pat)
    nra = _create_automaton(pat)
    if nra:
        nra = _unanchor_aut(nra)
    return nra

def create_rsa(pattern: str) -> Union[DRsA, bool]:
    nra = create_nra(pattern)
    if nra == False:
        return False
    #print(nra)
    nra = _unanchor_aut(nra)
    nra.remove_eps()
    nra.remove_unreachable()
    rsa = nra.determinize(postprocess=True)
    #print(rsa)
    if rsa == -1:
        return False
    else:
        return rsa