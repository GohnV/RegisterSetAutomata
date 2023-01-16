import RsA as rsa

#TODO: parsing and tree creation with sets on edges:
#      add set edges to normal parsing: [asdf] -> transition if a in {a, s, d, f} or [^asdf] -> transition if a not in {a, s, d, f}... 
#      parsing capturechar format: @. or @[asdf] or @[^a] etc
#      tree: capturechar should have a child containing the set of characters to be captured
#      determinization: create minterms as characters in set A
#   The last three should probably be done at the same time. First one can be done in advance

class Pair:
    type = ''
    data = ''
    def __init__(self, type, data):
        self.type = type
        self.data = data
    def createPair(self, symbol):
        if symbol in '&|*()$':
            self.type = symbol
            self. data = ''
        else:
            self.type = 'i'
            self.data = symbol

class Pushdown:
    data = []
    def push(self, item):
        for i in item.split():
            self.data.append(i)
    def top(self):
        return self.data[-1]
    def pop(self):
        return self.data.pop(-1)
    def topTerm(self):
        pass

def topTerm(list):
    for i in range(1,len(list)+1):
        if list[-i].type != 'E':
            return list[-i]

def rIndex(list, item):
    for i in range(1,len(list)+1):

        if list[-i].type == item.type:
            return len(list) - i   
    return -1       

def strAfterInd(list, index):
    str = ''
    for i in range(index+1, len(list)):
        if str == '':
            str = list[i].type
        else:
            str = str + ' ' + list[i].type
    return str

def createTree(expr):
    rules = ['E & E','E | E', 'E *', '( E )', 'i']
    dict = {'&':0, '|':1, '*':2, '(':3, ')':4, 'i':5, '$': 6}
    table = [['>', '>', '<', '<', '>', '<', '>'],
             ['<', '>', '<', '<', '>', '<', '>'],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['<', '<', '<', '<', '=', '<', '' ],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['>', '>', '>', '' , '>', '' , '>'],
             ['<', '<', '<', '<', '' , '<', '' ]]
    i = 0
    captCount = 0
    pushdown = [Pair('$','')]
    while True:
        a = topTerm(pushdown)
        ai = rIndex(pushdown, a)
        
        b = Pair('','')
        if (expr[i] == '.' and i+1 != len(expr) and expr[i+1] == '*'):
            b.createPair(rsa.SIGMASTAR)
            i += 1
        else:
            b.createPair(expr[i])
        '''
        print('a = ', a.type,',', 'ai = ', ai, end = ' ')
        print('b = ', b.type)
        print("start:", end=' ')
        for p in pushdown:
            print(p.type, end='')
        print()
        '''    
        #TODO: catch KeyError!!!!
        tblSymbol = table[dict[a.type]][dict[b.type]]
        #print("symbol:",tblSymbol)
        if tblSymbol == '=':
            pushdown.append(b)
            i += 1
        elif tblSymbol == '<':
            pushdown.insert(ai+1, Pair('<', ''))
            pushdown.append(b)
            i += 1  
        elif tblSymbol == '>':
            ind = rIndex(pushdown, Pair('<', ''))
            if ind != -1:
                string = strAfterInd(pushdown, ind)
                if string in rules:
                    # Vyrobeni konkretniho malyho stromu
                    #potom priradit strom do dat paru

                    tree= rsa.SyntaxTree()

                    if len(string) == 1:
                        tree.children = []
                        if pushdown[ind+1].data.isnumeric():
                            tree.data = rsa.BACKREFCHAR + pushdown[ind+1].data
                        elif pushdown[ind+1].data == '.':
                            tree.data = rsa.ANYCHAR
                        elif pushdown[ind+1].data == '@':
                            captCount += 1
                            tree.data = rsa.CAPTURECHAR + str(captCount)
                        elif pushdown[ind+1].data == rsa.SIGMASTAR:
                            tree.data = rsa.SIGMASTAR
                        else:
                            tree.data = pushdown[ind+1].data

                    elif string[0] == '(':
                        tree = pushdown[ind+2].data
                    #TODO: Tohle asi predelat, je to humus:
                    elif string[0] == 'E':
                        if string[2] == '*':
                            tree.data = rsa.ITERATION
                            tree.children = [pushdown[ind+1].data]
                        else:
                            tree.children = [pushdown[ind+1].data, pushdown[ind+3].data]
                            if string[2] == '&':
                                tree.data = rsa.CONCATENATION
                            elif string[2] == '|':
                                tree.data = rsa.UNION
                    #Odsataneni polozek ze zasobniku
                    for j in range(ind, len(pushdown)):
                        pushdown.pop(ind)
                    pushdown.append(Pair('E', tree))
                    #print('E ->', str)
                else:
                    print('chyba1')
                    return -1
            else:
                print('chyba2')
                return -1
        else:
            print('chyba3')
            return -1
        #print('i =', i,'expr[i] =', expr[i] )

        '''
        print('end:', end = ' ')
        for p in pushdown:
            print(p.type, end='')
        print()
        ''' 
        if (b.type == '$' and len(pushdown) == 2):
            if pushdown[0].type == '$' and pushdown[1].type == 'E':
                return pushdown[1].data
