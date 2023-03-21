import RsA as rsa
import graphviz

#draws the automaton as a pdf using graphviz
def drawAutomaton(aut, name):
    graph = graphviz.Digraph(name) 
    graph.format = 'pdf'
    graph.graph_attr["rankdir"] = "LR"
    graph.node('init_arrow', label = "", shape = 'none')
    q_shape = 'octagon'
    f_shape = 'doubleoctagon'
    if isinstance(aut, rsa.NRA):
        q_shape = 'circle'
        f_shape = 'doublecircle'
    eq_op = ' in ∈ '
    diseq_op = ' in ∉ '
    if isinstance(aut, rsa.NRA):
        eq_op = ' in = '
        diseq_op = ' in != '
    for q in aut.Q:
        qname = strIfMacroState(q)
        if q in aut.F:
            graph.node(qname, shape = f_shape)
        else:
            graph.node(qname, shape = q_shape)
    for t in aut.delta:
        regAssignment = ''
        for r in t.update.keys():
            upstr = str(t.update[r])
            #upstr = '{'
            #for up in t.update[r]:
            #    upstr += up+', '
            #upstr = upstr[:-2]
            #upstr += '}'
            regAssignment += ' '+str(r)+' ← ' + upstr+'\n'
        eqText = ''
        for g in t.eqGuard:
            eqText += '\n' + eq_op + str(g)
        diseqText = ''
        for g in t.diseqGuard:
            diseqText +='\n' + diseq_op + str(g)
        sym = str(t.symbol)
        if t.symbol == rsa.EPSILON:
            sym = 'ε'
        elif t.symbol == rsa.ANYCHAR:
            sym = 'Σ'
        elif t.symbol[0] == '^':
            sym = 'Σ \\\ ' + str(set(t.symbol[1]))
        else:
            sym = str(set(t.symbol[1]))
        oname = strIfMacroState(t.orig)
        dname = strIfMacroState(t.dest)
        graph.edge(oname, dname, label = ' ' + sym + eqText + diseqText + '\n' + regAssignment)
    for i in aut.I:
        iname = strIfMacroState(i)
        graph.edge('init_arrow', iname)
    #print(graph.source) into file!TODO:
    graph.render()

def strIfMacroState(q):
    ret = str(q)
    if isinstance(q, rsa.MacroState):
        smap = list(q.states)
        smap.sort()
        ret = str(smap)+'['
        for r in q.mapping.keys():
            ret = ret+str(r)+" "+str(q.mapping[r])+' | '
        ret+=']'
    return ret

def createGraph(tree, graph, id):
    datastr = str(tree.data)
    graph.node(datastr+str(id.count))
    currCount = id.count
    for i in range(len(tree.children)):
        id.count += 1 
        graph.edge(datastr+str(currCount), str(tree.children[i].data)+str(id.count))   
        createGraph(tree.children[i], graph, id)

def drawSyntaxTree(tree, name):
    id = rsa.Counter()
    graph = graphviz.Digraph(name)
    graph.format = 'svg'
    createGraph(tree, graph, id)
    graph.render()

