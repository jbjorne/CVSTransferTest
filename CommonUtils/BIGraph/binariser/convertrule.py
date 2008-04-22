import sys
import re
import yacc
import lex

########
# rule handling section
########

class Rule:
    @classmethod
    def write(cls,lh,rh,cut=False):
        result = []
        result.append("assert(")
        result.append("\trule(Level,GraphId) :-")
        result.append("\t(")
        # restrictions
        result.append("\t(")
        result.extend( Rule.processInput(lh) )
        result.append( "\tdifferent_nodes([%s])"%
                       ",".join(Rule.collectIds(lh)) )
        result.append("\t) ->")
        # prepare new level
        result.append("\t(")
        result.append("\tprepare_level(Level,GraphId,NewLevel),")
        # assertions
        result.extend( Rule.removeMatched(lh) )
        result.extend( Rule.processOutput(rh) )
        # rematch with new graph 
        if cut:
            result.append("\t!,")
        result.append("\tmatch(NewLevel,GraphId)")
        result.append("\t) ;")
        result.append("\tfail")
        result.append("\t)")
        result.append(").\n")
        result.append("\n") #ensures that dynamic predicate is finished
        return( (cut,result) )

    @classmethod
    def collectIds(cls,inlist):
        result = set()
        for a in [x for x in inlist if x.__class__==Formula]:
            result.add(a.uid)
            for b in a.args:
                result.update( Rule.collectIds(a.args) )
        return(result)
        
    @classmethod
    def processInput(cls,inlist):
        result = []
        for a in inlist:
            if a.__class__==Spec:
                result.append("\t%s(Level,GraphId,%s),"%(a.uid,
                                                         ','.join(a.args)))
            else:
                #result.append("\ttemp:node(Level,GraphId,%s,_,_,_),"%(a.uid))
                for b in a.args:
                    edgeid = ''.join([a.uid,b.uid])
                    result.append("\ttemp:edge(Level,GraphId,%s,%s,%s),"%
                                  (a.uid,
                                   b.uid,
                                   edgeid))
                    if b.edge:
                        result.append("\t%s = '%s',"%(edgeid,b.edge))
                result.extend( Rule.processInput(a.args) )
        return(result)

    @classmethod
    def removeMatched(cls,inlist):
        result = []
        for a in inlist:
            if not a.__class__==Spec:
                for b in a.args:
                    edgeid = ''.join([a.uid,b.uid])
                    result.append("\tretractall(temp:edge(NewLevel,GraphId,%s,%s,%s)),"%
                                  (a.uid,
                                   b.uid,
                                   edgeid))
                result.extend( Rule.removeMatched(a.args) )
        return(result)
        
    @classmethod
    def processOutput(cls,inlist):
        result = []
        for a in inlist:
            if a.__class__==Spec:
                result.append("\t%s(NewLevel,GraphId,%s),"%(a.uid,
                                                            ','.join(a.args)))
            else:
                for b in a.args:
                    if b.edge:
                        edgeid = "'%s'"%b.edge
                    else:
                        edgeid = ''.join([a.uid,b.uid])
                    result.append("\tassert(temp:edge(NewLevel,GraphId,%s,%s,%s)),"%
                                  (a.uid,
                                   b.uid,
                                   edgeid))
                result.extend( Rule.processOutput(a.args) )
        return(result)

        

class Formula:
    def __init__(self,uid,edge,args):
        self.uid = uid
        self.edge = edge
        self.args = args

class Spec:
    def __init__(self,uid,args):
        self.uid = uid
        self.args = args
        if self.uid[:4]=='not_':
            self.uid = '\+' + self.uid[4:]
    
# class Map:
#     def __init__(self,id_from,id_to):
#         self.id_from = id_from
#         self.id_to = id_to

# class Newtype:
#     def __init__(self,uid,newtype):
#         self.uid = uid
#         self.newtype = newtype

# class Newnested:
#     def __init__(self,uid,newnested):
#         self.uid = uid
#         self.newnested = newnested


########
# grammar section
########

# tokens
tokens = (
'ID',
'TXT',
'LIST',
'REGDIR',
#'MAP_TO',
#'NEW_TYPE',
#'NEW_NESTED',
'SEP_EDGE',
'BGN_ARGS',
'END_ARGS',
'SEP_ARGS',
'SEP_CMD',
'SEP_IO',
'SEP_IOCUT',
'END_RULE',
)

# regular expressions for tokens
t_ID = r'[A-Z]'
t_TXT = r'[A-Za-z][0-9A-Za-z-_\.]+'
t_LIST = r'\[.*\]'
t_REGDIR = r'[unp]'
#t_MAP_TO = r'%mapto%'
#t_NEW_TYPE = r'%type%'
#t_NEW_NESTED = r'%nested%'
t_SEP_EDGE = r':'
t_BGN_ARGS = r'\('
t_END_ARGS = r'\)'
t_SEP_ARGS = r','
t_SEP_CMD = r'\+'
t_SEP_IO = r'>>'
t_SEP_IOCUT = r'>>>>'
t_END_RULE = r';'

# error handling rule
def t_error(t):
    sys.stderr.write("Illegal character '%s'\n"%t.value[0])
    t.lexer.skip(1)

# comment handling rule
def t_comment(t):
    r'\#.*'
    pass

t_ignore=" \t\n"

# Error rule for syntax errors
def p_error(p):
    sys.stderr.write("Syntax error in input!\n")

# Rules
def p_rules(p):
    '''rules : rule END_RULE rules
             | rule END_RULE'''
    p[0] = [ Rule.write( p[1][0],p[1][1],cut=p[1][2] ) ]
    if len(p)==4:
        p[0] = p[0] + p[3]

def p_rule(p):
    '''rule : inputs SEP_IO outputs'''
    p[0] = ( p[1],p[3],False )

def p_rule2(p):
    '''rule : inputs SEP_IOCUT outputs'''
    p[0] = ( p[1],p[3],True )

def p_inputs(p):
    '''inputs : input SEP_CMD inputs
              | input SEP_CMD
              | input'''
    p[0] = [ p[1] ]
    if len(p)==4:
        p[0].extend(p[3])

def p_outputs(p):
    '''outputs : output SEP_CMD outputs
               | output SEP_CMD
               | output'''
    p[0] = [ p[1] ]
    if len(p)==4:
        p[0].extend(p[3])

def p_output(p):
    '''output : formula
             | spec'''
#              | map'''
    p[0] = p[1]

def p_input(p):
    '''input : formula
             | spec'''
    p[0] = p[1]

def p_formula1(p):
    '''formula : ID BGN_ARGS arguments END_ARGS'''
    p[0] = Formula(p[1],None,p[3])

def p_formula2(p):
    '''formula : TXT SEP_EDGE ID BGN_ARGS arguments END_ARGS'''
    p[0] = Formula(p[3],p[1],p[5])

def p_spec(p):
    '''spec : TXT BGN_ARGS texts END_ARGS'''
    p[0] = Spec(p[1],p[3])

# def p_map1(p):
#     '''map : ID MAP_TO ID'''
#     p[0] = Map(p[1],p[3])
    
# def p_map2(p):
#     '''map : ID NEW_TYPE TXT'''
#     p[0] = Newtype(p[1],p[3])
    
# def p_map3(p):
#     '''map : ID NEW_NESTED TXT'''
#     p[0] = Newnested(p[1],p[3])
    
def p_arguments(p):
    '''arguments : argument SEP_ARGS arguments
                 | argument'''
    p[0]=[ p[1] ]
    if len(p)==4:
        p[0].extend(p[3])

def p_argument1(p):
    '''argument : TXT SEP_EDGE ID'''
    p[0]=Formula(p[3],p[1],[])

def p_argument2(p):
    '''argument : formula'''
    p[0]=p[1]

def p_argument3(p):
    '''argument : ID'''
    p[0] = Formula(p[1],None,[])

def p_texts(p):
    '''texts : text SEP_ARGS texts
             | text'''
    p[0]=[ p[1] ]
    if len(p)==4:
        p[0].extend(p[3])

def p_text1(p):
    '''text : TXT'''
    p[0]="'%s'"%(p[1])

def p_text2(p):
    '''text : ID'''
    p[0]=p[1]

def p_text3(p):
    '''text : LIST'''
    p[0]=p[1]

def p_text4(p):
    '''text : REGDIR'''
    p[0]="'%s'"%(p[1])

########

def parse(string):
    lex.lex()
    yacc.yacc()
    rules = yacc.parse(string)

    result = []
    while rules:
        current = rules.pop(0)
        result.extend(current[1])
    return(result)

# The following orders cutting rules before non-cutting
#     cuts = []
#     nocuts = []
#     while rules:
#         current = rules.pop(0)
#         if current[0]:
#             cuts.extend(current[1])
#         else:
#             nocuts.extend(current[1])
#     return( cuts+nocuts )

if __name__=="__main__":
    import sys
    infile = open(sys.argv[1],'r')
    result = parse(infile.read())
    print '\n'.join(result)
