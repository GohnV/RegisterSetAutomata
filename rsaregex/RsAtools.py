#Author: Jan Vašák, 24.9.2022

import itertools as it
import networkx as nx
import copy
# from rsaregex.rsa_draw import draw_automaton

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

INSTR_DECODE = "DECODE"
INSTR_ACCEPT = "ACCEPT"
INSTR_FAIL = "FAIL"
INSTR_JUMP = "JUMP"
INSTR_TEST = "TEST"
INSTR_UPDATE = "UPDATE"
INSTR_ADDIN = "ADDIN"
INSTR_CLEAR = "CLEAR"
INSTR_SWAP = "SWAP"

class DeterminizationError(Exception):
    def __init__(self, message):
        super().__init__(message)

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
    # cachovat pro stejne mnoziny stavu
    n = len(sets)
    if n >= 1:
        tmp = sets[0]
        for i in range(1, n):
            tmp = rsa_set_intersection(tmp, sets[i])
        return tmp
    else:
        return MYEMPTY

#create minterms from sets of symbols as above
def _create_minterms_symb(sets):
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

def _intersect_n_sets(sets):
    '''intersects all sets specified in param sets'''
    n = len(sets)
    if n >= 1:
        tmp = sets[0]
        for i in range(1, n):
            tmp = tmp.intersection(sets[i])
        return tmp
    else:
        return set()

#create minterms from regular sets
#TODO: might be good for reduction of potential regs in powerset
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
            res = _intersect_n_sets(c)
            #print("res =", res)
            minterms.add(res)
            for i in range(n):
                sets[i] = sets[i].difference(res)
    #print(minterms)
    return minterms

# create a list of unicode ranges from myset of symbols
UNICODE_MIN = 0x0000
UNICODE_MAX = 0x10FFFF
SURR_START = 0xD800
SURR_END   = 0xDFFF
UNICODE_RANGE = [(UNICODE_MIN, SURR_START-1), (SURR_END+1, UNICODE_MAX)]
def _myset_to_ranges(myset):
    if myset == MYEMPTY:
        return []
    if myset == ANYCHAR:
        return UNICODE_RANGE
    out = []
    neg, charset = myset
    charlist = sorted(charset)
    l = r = ord(charlist[0])
    for c in charlist[1:]:
        c = ord(c)
        if c == r+1:
            r = c
        else:
            out.append((l,r))
            l = r = c
    out.append((l,r))

    #complement ranges if negated
    if neg == '^':
        compl = []
        for minl, maxr in UNICODE_RANGE:
            c = minl
            for l,r in out:
                # skip non-overlapping 
                if r < minl or l > maxr:
                    continue

                # clamp l and r into the range
                l = max(minl, l)
                r = min(maxr, r)

                if c < l:
                    compl.append((c, l-1))
                c = r+1
            if c <= maxr:
                compl.append((c, maxr))
        out = compl

    return out

class BDDTerm:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, BDDTerm):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

class BDDNode:
    def __init__(self, hi, lo, var, reg_id, parents: list):
        self.hi = hi
        self.lo = lo
        self.var = var
        self.reg_id = reg_id
        self.parents = parents

    def is_filled(self):
        return self.hi is not None and \
            self.lo is not None and \
            self.var is not None

    # def __eq__(self, value):
    #     return self is value

    # def __hash__(self):
    #     return hash(id(self))
    
    def get_key(self):
        return (id(self.hi), id(self.lo), self.var)
    

class MTBDD:
    def __init__(self):
        self.nodes = {} # a dict used like a set, but can retrieve the canonical value
                        # use nodes[node.get_key()] = node to add a node 
        self.terms = {}
        self.root = BDDNode(None, None, 0, None, set())

    def is_empty(self):
        return self.root.hi == None and self.root.lo == None

    def create_term(self, value):
        newterm = BDDTerm(value)
        tmp = self.terms.get(newterm)
        if tmp is None: #add new node
            self.terms[newterm] = newterm
        else:
            newterm = tmp #replace with canonical node
        return newterm
                

    def create_node(self, var, reg_id, parent):
        return BDDNode(None, None, var, reg_id, {parent})            

    def add_path(self, var_values: list, term_value):
        # terms are easy, but should I create
        node = self.root
        nvars = len(var_values)
        if nvars > 0 and node.reg_id is None: #fill root id if missing
            node.reg_id = var_values[0][0]
        for i, (_,x) in enumerate(var_values):
            # print(i,x)
            # TODO: make a function like create_child(self, vard_idx, nvars, term_value)?
            if x: #go high
                if node.hi is not None:
                    next_node = node.hi
                else:
                    if i == nvars-1: # newnode will be term
                        node.hi = self.create_term(term_value)
                        return
                    else:
                        node.hi = self.create_node(i+1, var_values[i+1][0], node) #var_values[i+1][0] is the reg_id of the next node
                        next_node = node.hi
            else: #go low
                if node.lo is not None:
                    next_node = node.lo
                else:
                    if i == nvars-1: #newnode will be term
                        node.lo = self.create_term(term_value)
                        return
                    else:
                        node.lo = self.create_node(i+1,var_values[i+1][0], node)
                        next_node = node.lo
            # if node.is_filled():
            #     self.store_node(node)
            node = next_node

    def create_level_arr(self, nvars):
        arr = [set() for _ in range(nvars)]
        curr = self.root
        self.create_level_arr_impl(arr, curr)
        return arr

    def create_level_arr_impl(self, arr, curr):
        if isinstance(curr, BDDTerm):
            return
        arr[curr.var].add(curr)
        self.create_level_arr_impl(arr, curr.hi)
        self.create_level_arr_impl(arr, curr.lo)

    def remove_dupl_nodes(self, nvars):
        merged = False
        level_arr = self.create_level_arr(nvars)
        self.nodes = {} #clear
        for nodelist in reversed(level_arr): #start with lowest level (=> children must be stored already)
            for node in nodelist:
                table_node = self.nodes.get(node.get_key())
                if table_node is None:
                    self.nodes[node.get_key()] = node
                else: # MERGING into table node
                    merged = True
                    #re-route edges to new node
                    for p in node.parents:
                        if p.hi is node:
                            p.hi = table_node
                        if p.lo is node:
                            p.lo = table_node
                        table_node.parents.add(p)
                    for child in [node.hi, node.lo]:
                        if isinstance(child, BDDNode):
                            child.parents.discard(node) #id lo == hi we get in trouble remove
                            child.parents.add(table_node)
        return merged
    
    def delete_useless_nodes_impl(self, curr):
        if isinstance(curr, BDDTerm):
            return False
        if curr.hi == curr.lo: #delete this node
            child = curr.hi # we can use lo or hi
            if isinstance(child, BDDNode):
                child.parents.remove(curr)
            for p in curr.parents:
                if p.lo is curr:
                    p.lo = child
                if p.hi is curr:
                    p.hi = child
                if isinstance(child, BDDNode):
                    child.parents.add(p)
            if curr == self.root:
                self.root = child
            self.delete_useless_nodes_impl(child)
            return True #we deleted so true no matter what

        else:
            rethi = self.delete_useless_nodes_impl(curr.hi)
            retlo = self.delete_useless_nodes_impl(curr.lo)
            return rethi or retlo

    def delete_useless_nodes(self):
        return self.delete_useless_nodes_impl(self.root)

    def reduce(self, nvars):
        changed = True
        while changed:
            changed = False
            merged = self.remove_dupl_nodes(nvars)
            deleted = self.delete_useless_nodes()
            changed = merged or deleted

    def write_code(self, prg: list, prefix: str):
        id_map = {}
        written = set()
        self.write_code_impl(self.root, prg, id_map, written, prefix)
    
    def write_code_impl(self, node: BDDNode, prg: list, id_map: dict, written: set, prefix: str):
        def get_id(n):
            nid = id_map.get(n)
            if nid is None:
                nid = len(id_map)
                id_map[n] = nid
            return nid
        
        def get_label(succ):
            if isinstance(succ, BDDNode):
                return prefix+"_node_"+str(get_id(succ))
            else:
                assert(isinstance(succ, BDDTerm))
                return prefix+f"_{succ.value}"

        assert(isinstance(node, BDDNode))
        if node not in written:
            prg.append(f"{get_label(node)}:")
            written.add(node)
        hi_lab = get_label(node.hi)
        lo_lab = get_label(node.lo)
        prg.append(INSTR_TEST+f" {node.reg_id} {hi_lab}")
        prg.append(INSTR_JUMP+f" {lo_lab}")
        for succ in [node.hi, node.lo]:
            if isinstance(succ, BDDNode):
                self.write_code_impl(succ, prg, id_map, written, prefix)

class DecodeTreeNode:
    def __init__(self):
        self.children = []
        self.label = None
    
    def init_children(self, nclasses):
        self.children = [None for _ in range(nclasses)]

def _serialize_decode_tree(node):
    if node is None: #for safety
        return None

    if node.children != []:
        node.label = None 

        return {
            "label": node.label,
            "children": [
                _serialize_decode_tree(child) for child in node.children
            ]
        }
    elif node.label == None:
        return {
            "label" : -1
        }
    else:
        return {
            "label" : node.label
        }

def _check_char_in_decode_tree(char, tree: DecodeTreeNode, bytemap):
    chbytes = char.encode("utf-8")
    curr = tree
    for b in chbytes:
        b = bytemap[b] #work with byteclass
        if curr == None:
            return -1
        curr = curr.children[b] #descend
    return curr.label

def _add_char_to_decode_tree(char, tree: DecodeTreeNode, leafptrarr, bytemap, nclasses):
    #assumes char is not already in tree, and that tree is not None
    assert(tree != None)
    chbytes = char.encode("utf-8")
    curr = tree
    for b in chbytes:
        b = bytemap[b] #work with byteclass
        if curr.children == []:
            curr.init_children(nclasses)
        if curr.children[b] == None: #uninitialized child
            curr.children[b] = DecodeTreeNode()
        curr = curr.children[b] #descend
    #decoded, number the leaf
    idx = len(leafptrarr)
    curr.label = idx
    leafptrarr.append(curr)
    return idx

def _pad_arr_to_idx(arr, idx, val=0):
    arr.extend([val] * (idx + 1 - len(arr)))

def _find_dangling(tree: DecodeTreeNode, dangling):
    for i in range(len(tree.children)):
        if tree.children[i] == None:
            newnode = DecodeTreeNode()
            tree.children[i] = newnode
            dangling.append(newnode)
        else:
            _find_dangling(tree.children[i], dangling)

def _generate_decode_tree(charsets, bytemap, nclasses, state_id):
    processed_chars = {}
    decode_tree = DecodeTreeNode()
    leafptrarr = []
    leafmaps = [[] for _ in charsets] #TODO: leafmaps could be bitarrays
    seen_neg = False

    # create tree structure by adding all characters first
    for myset in charsets.keys():
        neg, chset = myset
        if neg == "^":
            seen_neg = True
        for ch in chset:
            leafarr = leafmaps[charsets[myset]]
            if ch in processed_chars.keys():
                idx = processed_chars[ch]
            else:
                idx = _add_char_to_decode_tree(ch, decode_tree, leafptrarr, bytemap, nclasses)
                processed_chars[ch] = idx
            if idx >= len(leafarr):
                _pad_arr_to_idx(leafarr, idx)
            leafarr[idx] = 1
    
    # find dangling leaves
    dangling = []
    if seen_neg:
        _find_dangling(decode_tree, dangling)


    #assign labels correctly
    for myset in charsets.keys():
        neg, _ = myset
        yesval = 0 if neg == "^" else 1
        setnum = charsets[myset]
        map = leafmaps[setnum]
        for i in range(len(map)):
            if map[i] == yesval:
                leafptrarr[i].label = f"{state_id}_{setnum}"
        # add label to dangling ends
        if neg == "^":
            for d in dangling:
                d.label = f"{state_id}_{setnum}"
    return decode_tree



def remove_update_cycles(graph: nx.DiGraph):
    sccs = list(nx.strongly_connected_components(graph))
    next_reg_id = 0
    old_to_new = {}
    new_to_old = {}
    # if graph is NOT acyclic, split some nodes
    while len(sccs) < graph.number_of_nodes():        
        to_split = []
        for nodes in sccs:
            if len(nodes) > 1:
                # add node with max out degree
                to_split.append(max(nodes, key=lambda n: graph.out_degree(n)))
        for node in to_split:
            new_node = f"free_{next_reg_id}"
            next_reg_id += 1
            old_to_new[node] = new_node
            new_to_old[new_node] = node
            outgoing = list(graph.out_edges(node))

            graph.add_node(new_node)
            for _, v in outgoing:
                graph.add_edge(new_node, v)
            graph.remove_edges_from(outgoing)
        # new sccs from the updated graph
        sccs = list(nx.strongly_connected_components(graph))
    return old_to_new, new_to_old

def create_update_graph(upd_list):
    graph = nx.DiGraph()
    for r, rhs in upd_list:
        graph.add_node(r)
        for x in rhs:
            if x == r or x == IN:
                continue
            graph.add_edge(r, x)
    return graph

def transform_updates(upd_list):
    #reconstruct update:
    update = {k:v for k,v, in upd_list}
    #build update graph and remove cycles by splitting
    # updates into reg_new <- update[reg], reg <- reg_new
    graph = create_update_graph(upd_list)
    old_to_new, new_to_old = remove_update_cycles(graph)
    # order updates based on dependencies
    order = list(nx.topological_sort(graph))
    
    #rebuild updates from upd_list in the correct order
    updates_new = list()
    for node in order:
        if node in old_to_new.keys():
            # reg <- reg_new
            updates_new.append((node, {old_to_new[node]}))
        elif node in new_to_old.keys():
            old = new_to_old[node]
            updates_new.append((node, update[old]))
        else:
            updates_new.append((node, update[node]))
    return updates_new


    

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

def _freeze_update(upd):
    return frozenset({(rhs,frozenset(lhs)) for rhs,lhs in upd.items()})

class MacroState:
    def __init__(self):
        self.states = set()
        self.mapping = {}

    def key(self):
        return (frozenset(self.states), frozenset(self.mapping.items()))


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

    def outgoing_trans(self,q):
        ret = set()
        for t in self.delta:
            if t.orig == q:
                ret.add(t)
        return ret
    
    def incoming_trans(self,q):
        ret = set()
        for t in self.delta:
            if t.dest == q:
                ret.add(t)
        return ret

    def remove_eps(self):
        '''removes epsilon transitions'''
        deltaNew = set()
        newF = set()
        to_remove = set()

        # if the ONLY outoging transition is epsilon
        # we can simply merge this state into the next
        for q in self.Q:
            # removing final states is difficult,
            # since in general we cannot move finality
            # to the next state
            if q in self.F:
                continue

            outgoing = self.outgoing_trans(q)
            
            if len(outgoing) == 1:
                only_trans = next(iter(outgoing))
                if only_trans.symbol == EPSILON:
                    to_remove.add(q)
                    if q in self.I:
                        self.I.remove(q)
                        self.I.add(only_trans.dest)
                    # re-route transitions
                    for t in self.incoming_trans(q):
                        t.dest = only_trans.dest
        for q in to_remove:
            self.Q.remove(q)
        
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
    """Class representing a DRsA.    
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

    def _create_state_id_map(self):
        return {s.key() : i for i, s in enumerate(self.Q)}

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
    
    #tests guards of a transition
    def _create_memb_map(self, input, regConf,):
        memb_map = dict()
        for r in self.R:
            if input in regConf[r]:
                memb_map[r] = True
            else:
                memb_map[r] = False
        return memb_map
    
    #tests guards of a transition
    def _test_memb_map(self, memb_map, eqG, diseqG):
        for g in eqG:
            if not memb_map[g]:
                return False
                
        for g in diseqG:
            if memb_map[g]:
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
            #TODO: do one test and then check the bitmap with transitions
            for t in self.trans_dict[(frozenset(c.states),frozenset(c.mapping.items()))]:
                if rsa_is_char_in(s, t.symbol) and self._guard_test(s, regConf, t.eqGuard, t.diseqGuard):
                    #if found:
                        # print("FOUND DUPLICATE:")
                        # print(trans_f.orig, trans_f.orig.states, trans_f.orig.mapping, trans_f.symbol, trans_f.eqGuard, trans_f.diseqGuard, trans_f.update)
                        # print(t.orig, t.orig.states, t.orig.mapping, t.symbol, t.eqGuard, t.diseqGuard, t.update)
                        #pass
                    found = True
                    trans_f = t
                    break
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
                # up_aux maps a register to the classes its updated with
                up_aux = {}
                up_new = {}
                # build up_aux
                for r in self.R:
                    Y = set()
                    for y in t.update[r]:
                        # find class of y
                        if y != IN:
                            for C in P:
                                if y in C:
                                    y = C
                                    break
                        Y.add(y)
                    up_aux[r] = Y
                # build new partition
                for Y in up_aux.values():
                    C1 = set()
                    for r in self.R:
                        if up_aux[r] == Y:
                            C1.add(r)
                    if Y != set():
                        P1.add(frozenset(C1))
                    up_new[frozenset(C1)] = Y

                # build (n)eq guard
                g_eq_new = set()
                g_neq_new = set()
                for C in P:
                    for r in C:
                        if r in t.eqGuard:
                            g_eq_new.add(C)
                        if r in t.diseqGuard:
                            g_neq_new.add(C)

                # make sure register list is complete
                for C in P1:
                    Rnew.add(C)

                # check whether created state already exists, and add it if not
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
                
                # check overapprox on the created transition
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
                            # print(t1.orig,"->", t1.dest,"| up =", t1.update)
                            if t1.dest != q1:
                                continue
                            found = True
                            for y in elem:
                                if t1.update[y[0]] not in y[1]:
                                    found = False
                                    break
                            if found:
                                # print("found")
                                break
                        if not found:
                            # draw_automaton(DRsA(Qnew, Rnew, deltaNew, Inew, set()), "postprocessed")
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


    def _create_bytemap(self):
        #DEBUG: trivial bytemap
        return [i for i in range(256)], 256

    def generate_vm_code(self):

        # TODO: cleanup interface
        self.remove_eps()
        self.remove_unreachable()
        drsa = self.determinize(postprocess=True) #let it crash if non-determinizable for now
        statemap = drsa._create_state_id_map()
        prg = []
        bytemap, nclasses = self._create_bytemap()
        mem = [None for _ in drsa.Q]
        reglist = sorted(drsa.R) # establish fixed order
        regmap = {r:i for i, r in enumerate(reglist)} | \
            {f"free_{i}":len(reglist)+i for i in range(len(reglist))}
        assert(len(drsa.I) == 1)
        init_state = next(iter(drsa.I))
        drsa.Q.remove(init_state)
        for s in [init_state, *drsa.Q]:

            tdkey = (frozenset(s.states),frozenset(s.mapping.items()))
            state_id = statemap[s.key()]
            prg.append(f"state_{state_id}:") #label

            #FIXME: implement eq and hash methods for state! so this doesn't happen
            for f in drsa.F:
                if s.states == f.states and s.mapping == f.mapping:
                    prg.append(INSTR_ACCEPT)
                    break

            # no transitions to decode
            if drsa.trans_dict[tdkey] == set():
                prg.append(INSTR_FAIL)
                continue

            prg.append(INSTR_DECODE + f" {state_id}")
            
            # group transitions from s by symbol
            charsets = {}
            charsetcnt = 0
            charset_trans = {}
            for t in drsa.trans_dict[tdkey]:
                if t.symbol not in charsets.keys():
                    charsets[t.symbol] = charsetcnt
                    charset_trans[charsetcnt] = []
                    charsetcnt += 1
                idx = charsets[t.symbol]
                charset_trans[idx].append(t)
            decode_tree = _generate_decode_tree(charsets, bytemap, nclasses, state_id)
            mem[state_id] = _serialize_decode_tree(decode_tree)
            # TODO: if too slow, serialize into binary

            for chidx in charset_trans.keys(): #iterate over groups of transitions
                prg.append(f"{state_id}_{chidx}:")
                mtbdd = MTBDD()
                uniq_trans = {}
                #decide transition
                for t in charset_trans[chidx]:
                    trans_key = (_freeze_update(t.update), statemap[t.dest.key()])
                    trans_id = uniq_trans.get(trans_key)
                    if trans_id is None:
                        trans_id = len(uniq_trans)
                        uniq_trans[trans_key] = trans_id

                    var_values = []
                    for r in reglist: #build vector for mtbdd
                        if r in t.eqGuard:
                            var_values.append((regmap[r], 1))
                        elif r in t.diseqGuard:
                            var_values.append((regmap[r], 0))
                    mtbdd.add_path(var_values, trans_id)
                if len(uniq_trans) > 1:
                    # dump_mtbdd(mtbdd)
                    mtbdd.reduce(len(var_values))

                    mtbdd.write_code(prg, f"{state_id}_{chidx}")

                    #print transition update and move
                for trans_key, trans_id in uniq_trans.items():
                    upd, dest_id = trans_key
                    upd = transform_updates(upd)
                    prg.append(f"{state_id}_{chidx}_{trans_id}:") #label
                    for lhs,rhs in upd:
                        rhs = set(rhs) # unfreeze set

                        if len(rhs) == 1:
                            item = next(iter(rhs))
                            if item.startswith("free"):
                                prg.append(INSTR_SWAP+f" {regmap[lhs]} {regmap[item]}")
                                continue

                        if lhs not in rhs:
                            if lhs in s.mapping.keys() and s.mapping[lhs] > 0:
                                prg.append(INSTR_CLEAR+f" {regmap[lhs]}")
                        else:
                            rhs.remove(lhs)
                        
                        addin = False
                        if IN in rhs:
                            addin = True
                            rhs.remove(IN)

                        if len(rhs) > 0:
                            str_rhs = " ".join([str(regmap[r]) for r in rhs])
                            prg.append(INSTR_UPDATE+" "+str(regmap[lhs])+" "+str_rhs)

                        if addin:
                            prg.append(INSTR_ADDIN + f" {regmap[lhs]}")

                    prg.append(INSTR_JUMP+f" state_{dest_id}")

            prg.append(INSTR_FAIL)
        return prg, mem, len(regmap)

    def determinize(self, postprocess=False, track_sizes=True) -> DRsA:
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
            regs0 = set()
            sets = set()
            for t in self.delta:
                if t.orig in sc.states:
                    sets.add(t.symbol)
                    regs0 = regs0.union(t.eqGuard)
            #print(sets)
            regs = set()
            for r in regs0:
                if sc.mapping[r] != 0:
                    regs.add(r)

            #create minterms of all transitions used for a given set of states into A
            A = _create_minterms_symb(list(sets))
            #TODO: add mintermification before powerset to 'join' some registers if there's no reason to separate them
            #       maybe also try that^ for the whole regex?
            #TODO: what about BDDs?
            G = set(powerset(regs))
            #print(A)
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
                                    #print("overapproxes")
                                    overapprox = True
                                    if not postprocess:
                                        raise DeterminizationError("Overapproximation detected")
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
                            c_aux = 1 if x == IN else sc.mapping[x]
                            cnt |= c_aux
                        c1[ri] = cnt
                    s1c1 = MacroState()
                    s1c1.states = S1
                    s1c1.mapping = c1
                    found = False
                    #TODO: optimize this membership test if possible
                    for q1 in newA.Q:
                        #orig:
                        if s1c1.states == q1.states and s1c1.mapping == q1.mapping:
                            found = True
                            break
                    if not found:
                        worklist.append(s1c1)
                        newA.add_q(s1c1)
                    newA.add_transition(Transition(sc, a, g, regs.difference(g), up1, s1c1))
        #accepting states:
        for mq in newA.Q:
            for q in mq.states:
                if q in self.F:
                    newA.add_f(mq)
                    break
        if postprocess and overapprox:
            # if postprocess also detects overapprox, abort
            if not newA.postprocess(self):
                raise DeterminizationError("Overapproximation detected")
                return -1
        newA.trans_dict = newA._create_trans_dict()
        return newA
#end of class NRA
