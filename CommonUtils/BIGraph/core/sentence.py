import sys
import inspect
import cElementTree as ET
import networkx as NX
from BIGraph import *
    
class Element(SimpleElement):
    """
    Basic element within a sentence. The id is in form
    <type>.<sentenceId>.<runningId> for each element.
    """
    def __init__(self,**kwargs):
        SimpleElement.__init__(self,**kwargs)

    def getPrefix(self):
        """
        Returns the element type prefix.

        @return: prefix
        @rtype: string
        """
        return( self.id.split('.')[0] )
        
    def getSentenceId(self):
        """
        Returns the sentence id of the element.

        @return: sentence id
        @rtype: integer
        """
        return( int(self.id.split('.')[1]) )

    def getRunningId(self):
        """
        Returns the running id of the element.

        @return: sentence id
        @rtype: integer
        """
        return( int(self.id.split('.')[2]) )

class Subtoken(Element):
    """
    Element for 'subtoken' nodes. Additional attributes:
    'offset_bgn','offset_end','text'
    """
    def __init__(self,**kwargs):
        Element.__init__(self,**kwargs)
        self.setVars( ['offset_bgn','offset_end','text'],
                      **kwargs )
    
    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Element.getNode(self)
        node.tag = 'subtoken'
        return(node)

    def getUniStr(self):
        """
        Returns a unique string identifying the subtoken.

        @return: unique string
        @rtype: string
        """
        return("%s.%s.%s-%s"%(self.getPrefix,self.getSentenceId,
                              self.offset_bgn,self.offset_end))
    
class Token(Element):
    """
    Generic element for token nodes. Nests subtokens and keep record
    of 'special' subtokens.
    """
    def __init__(self,**kwargs):
        Element.__init__(self,**kwargs)
        self.nested = set()
        self.special = set()
        
    def addSubtoken(self,subtoken,special=False):
        """
        Adds a subtoken.

        @param subtoken: subtoken element
        @type subtoken: Subtoken
        @param special: special flag
        @type special: boolean
        """
        self.nested.add(subtoken)
        if special:
            self.special.add(subtoken.id)

    def removeSubtoken(self,subtoken):
        """
        Removes a subtoken.

        @param subtoken: subtoken element
        @type subtoken: Subtoken
        """
        self.nested.remove(subtoken)
        if subtoken.id in self.special:
            self.special.remove(subtoken.id)
        
    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Element.getNode(self)
        node.tag = 'token'
        del node.attrib['nested']
        del node.attrib['special']
        for a in self.getNested():
            special = str(a.id in self.special)
            node.append(ET.Element("nestedsubtoken",
                                   subtoken=a.id,
                                   special=special))
        return(node)
    
    def getNested(self):
        """
        Returns the nested subtokens (Subtoken objects) in the linear
        order.

        @return: nested subtokens
        @rtype: list
        """
        result = list(self.nested)
        result.sort(lambda x,y: x.getRunningId()-y.getRunningId())
        return(result)
        
    def getSpecial(self):
        """
        Returns the nested subtokens (Subtoken objects) in the linear
        order.

        @return: nested subtokens
        @rtype: list
        """
        return( [x for x in self.getNested() if x.id in self.special] )
        
    def getText(self):
        """
        Returns the concatenation of the texts of the nested subtokens.
        
        @return: text of the token
        @rtype: string
        """
        return(' '.join(map(lambda x:x.text,self.getNested())))

    def getUniStr(self):
        """
        Returns a string unique to the token. The string is a
        concatenation of the type of the token and the ids of the
        nested subtokens.
        
        @return: unique string
        @rtype: string
        """
        return('-'.join(["%s-%s"%(x.id,(x.id in self.special))
                         for x in self.getNested()]))
        
class DepToken(Token):
    """
    Element for 'deptoken' nodes.
    """
    def __init__(self,**kwargs):
        Token.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Token.getNode(self)
        node.tag = 'deptoken'
        return(node)
        
class RelToken(Token):
    """
    Element for 'reltoken' nodes.
    """
    def __init__(self,**kwargs):
        Token.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Token.getNode(self)
        node.tag = 'reltoken'
        return(node)

class Entity(Element):
    """
    Generic element for entity nodes.
    """
    def __init__(self,**kwargs):
        """
        'token' argument must be Token (or subclass) instance.
        """
        Element.__init__(self,**kwargs)
        self.setVars(['token','type'],**kwargs)
    
    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Element.getNode(self)
        node.tag = 'entity'
        node.attrib['token'] = self.token.id
        return(node)

    def getUniStr(self):
        """
        Returns a unique string identifying the entity.

        @return: unique string
        @rtype: string
        """
        return("%s/%s"%(self.token.id,self.type))

class RelEntity(Entity):
    """
    Element for 'relentity' nodes. Additional attributes:
    'meta_annotation','semanticId','isName'
    """
    def __init__(self,**kwargs):
        Entity.__init__(self,**kwargs)
        self.setVars(['meta_annotation','semanticId','isName'],**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Entity.getNode(self)
        node.tag = 'relentity'
        return(node)

    def getUniStr(self):
        """
        Returns a unique string identifying the entity.

        @return: unique string
        @rtype: string
        """
        return("%s/%s"%(Entity.getUniStr(self),self.semanticId))

class DepEntity(Entity):
    """
    Element for 'depentity' nodes.
    """
    def __init__(self,**kwargs):
        Entity.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Entity.getNode(self)
        node.tag = 'depentity'
        return(node)

class Node(Element):
    """
    Generic element for graph nodes. Represents one entity.
    """
    def __init__(self,**kwargs):
        """
        'entity' argument must be Entity (or subclass) instance.
        """
        Element.__init__(self,**kwargs)
        self.setVars(['entity'],**kwargs)
    
    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Element.getNode(self)
        node.tag = 'node'
        node.attrib['entity'] = self.entity.id
        return(node)

class DepNode(Node):
    """
    Element for depnode nodes.
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'depnode'
        return(node)
        
class RelNode(Node):
    """
    Element for relnode nodes.
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'relnode'
        return(node)
        
class Edge(Element):
    """
    Generic element for edge nodes. Adds attributes
    'type','bgn','end'.
    """
    def __init__(self,**kwargs):
        """
        'bgn' and 'end' arguments must be Node (or subclass) instances.
        """
        Element.__init__(self,**kwargs)
        self.setVars(['type','bgn','end'],**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Element.getNode(self)
        node.tag = 'edge'
        node.attrib['bgn'] = self.bgn.id
        node.attrib['end'] = self.end.id
        return(node)

class DepEdge(Edge):
    """
    Element for depedge nodes. Extends Edge by adding attributes
    'category','linkage','status'.
    """
    def __init__(self,**kwargs):
        Edge.__init__(self,**kwargs)
        self.setVars(['category','linkage','status'],
                     **kwargs)
        
    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Edge.getNode(self)
        node.tag = 'depedge'
        return(node)
        
class RelEdge(Edge):
    """
    Element for reledge nodes.
    """
    def __init__(self,**kwargs):
        Edge.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns the element as cElementTree.Element.

        @return: element as a node
        @rtype: cElementTree.Element
        """
        node = Edge.getNode(self)
        node.tag = 'reledge'
        return(node)
        
class Sentence(SimpleElement):
    """
    The sentence class stores and handles the sentence-level data. The
    original ET.Element object (tagged 'sentence') is not
    stored. Sentence object itself is Element (extended by
    'PMID','text', and 'relaxed_annotators' attributes).

    The attributes of the sentence node are stored as instance
    variables. The subtokens are stored in a dictionary keyed by the
    subtoken id. Similarly reltokens and deptokens are keyed by their
    ids. Subtokens as well as both deptokens and reltokens are unique
    within the object. Tokens are typed sets of subtokens.
    
    Both the syntactic annotation and the interaction annotation are labeled
    directed graphs. 

    The syntactic annotation is stored in a networkx.XDiGraph object as
    follows:
      - nodes in the graph are DepNode objects which link to DepToken objects
      - edges are labeled with DepEdges that contain the link information
    
    The interaction annotation is stored in a networkx.XDiGraph object
    similarly to syntactic annotation:
      - note that one reltoken can have several instances in the graph
        (as different relnodes)

    In summary, all data is copied into new objects. Subtokens and
    tokens can acccessed through a dictionary while nodes and edges
    through the graphs.
    """
    def __init__(self,**kwargs):
        SimpleElement.__init__(self,**kwargs)
        self.setVars( ['PMID','text'],
                      **kwargs )
        
        self.subtokens = {}
        """dict of subtokens """
        self.deptokens = {}
        """dict of dependency tokens """
        self.reltokens = {}
        """dict of interaction tokens """
        self.depentities = {}
        """dict of dependency tokens """
        self.relentities = {}
        """dict of interaction tokens """
        
        # depNodes and depEdges are stored in a graph
        self.dependencies = NX.XDiGraph(multiedges=True)
        # relNodes and relEdges are stored in a graph
        self.interactions = NX.XDiGraph(multiedges=True)

    def newElement(self,cls,attrib={}):
        """
        A new element (subtoken,token,entity,node,edge) is created and a free
        id is automatically given. Subtokens, tokens, and entities are also added
        to the dictionary but nodes and edges must be added to the
        corresponding graph manually.

        @param cls: the class of the new element
        @type cls: any subclass of Element
        @param attrib: additional parameters to the new element
        @type attrib: dictionary
        @return: the new element
        @rtype: the object of class 'cls'
        """
        elem = cls(**attrib)
        self.setFreeId(elem)
        if cls==Subtoken:
            self.subtokens[elem.id] = elem
        elif cls==DepToken:
            self.deptokens[elem.id] = elem
        elif cls==RelToken:
            self.reltokens[elem.id] = elem
        elif cls==DepEntity:
            self.depentities[elem.id] = elem
        elif cls==RelEntity:
            self.relentities[elem.id] = elem
        else:
            # It is caller responsibility to add elements to the graph
            pass
        
        return(elem)

    def copyElement(self,elem):
        """
        A new element (subtoken,token,entity,node,edge) is created
        with newElement-method such that the new element is a
        (shallow) copy of the original.

        @param elem: the element to be copied
        @type elem: any subclass of Element
        @return: the new element
        @rtype: the object of the same class as 'elem'
        """
        return( self.newElement(elem.__class__,elem.__dict__) )

    # function to make a copy of node in graph
    # such that its contents does not change
    def copyRelNode(self,node):
        """
        RelNode object is cloned in such a way that both the original
        and the copy have the exactly same context in the graph as the
        original had be cloning.

        NOT RELIABLE IMPLEMENTATION

        @param node: the original node
        @type node: RelNode
        @return: the copy
        @rtype: RelNode
        """
        G = self.interactions
        
        newNode = self.newElement(RelNode,node.__dict__)
        # out-going edges never interfere between copies
        for (p1,p2,u) in G.out_edges(node):
            newEdge = self.newElement(RelEdge,u.__dict__)
            newEdge.bgn = newNode
            G.add_edge(newNode,p2,newEdge)

        # collect in-coming edges by type
        inCopy = {}
        for b in G.in_edges(node):
            typ = b[2].type
            if not inCopy.has_key(typ):
                inCopy[typ] = set()
            inCopy[typ].add(b[0])
        if inCopy.has_key('agpat'):
            agpats = inCopy.pop('agpat')
        else:
            agpats = []

        # non-agpat in-coming edges can be just copied
        for (k,v) in inCopy.items():
            for p1 in v:
                newEdge = self.newElement(RelEdge)
                newEdge.type = k
                newEdge.bgn = p1
                newEdge.end = newNode
                G.add_edge(p1,newNode,newEdge)

        # make copies of agpat parents (to avoid agpat between aliases)
        for a in agpats:
            newNode2 = self.copyRelNode(a)
            for b in [x for x in G.out_edges(newNode2) if x[1]==node]:
                G.delete_edge(b)
                b[2].end = newNode
                G.add_edge(newNode2,newNode,b[2])

        return(newNode)

    def prune(self):
        # add components as necessary

        # remove relentities and reltokens that not linked to the
        # interaction graph
        usedRbs = set(x.entity for x in self.interactions.nodes())
        delme = set()
        saveme = set()
        for entity in self.relentities.values():
            if not entity in usedRbs:
                del self.relentities[entity.id]
                delme.add(entity.token)
                printMessage(self.__class__,
                             inspect.stack()[0][3],
                             "Removed unused relentity %s"%(entity.id))
            else:
                saveme.add(entity.token)
        for token in delme-saveme:
            del self.reltokens[token.id]
            printMessage(self.__class__,
                         inspect.stack()[0][3],
                         "Removed unused reltoken %s"%(token.id))
    
# ----
# Set/get functions
# ----

    def setFreeId(self,element):
        """
        Sets the id of 'element' to a free and valid id within the
        sentence instance.

        @param element: Element to be changed
        @type element: any subclass of Element
        """
        if element.__class__==Subtoken:
            prefix = 'st'
            inlist = self.subtokens.values()
        elif element.__class__==DepToken:
            prefix = 'dt'
            inlist = self.deptokens.values()
        elif element.__class__==RelToken:
            prefix = 'rt'
            inlist = self.reltokens.values()
        elif element.__class__==DepEntity:
            prefix = 'db'
            inlist = self.depentities.values()
        elif element.__class__==RelEntity:
            prefix = 'rb'
            inlist = self.relentities.values()
        elif element.__class__==DepNode:
            prefix = 'dn'
            inlist = self.dependencies.nodes()
        elif element.__class__==RelNode:
            prefix = 'rn'
            inlist = self.interactions.nodes()
        elif element.__class__==DepEdge:
            prefix = 'de'
            inlist = [x[2] for x in self.dependencies.edges()]
        elif element.__class__==RelEdge:
            prefix = 're'
            inlist = [x[2] for x in self.interactions.edges()]
        else:
            inlist = []
            printWarning(self.__class__,
                         inspect.stack()[0][3],
                         "%s should not have id"%(element.__class__))
        used = map(lambda x:x.getRunningId(),inlist)
        element.id = '.'.join([prefix, self.id, FreeIdIter(used).get()])
        return(True)
    
    def setNode(self,node):
        """
        Sets the data from 'node' into the instance.

        @param node: The sentence node from which data is collected
        @type  node: ET.Element 'sentence'
        """
        Sentence.__init__(self,**node.attrib)

        tmpSts = node.find("subtokens")
        tmpDep = node.find("depannotation")
        tmpRel = node.find("relannotation")
        
        # generate subtokens
        for a in tmpSts.findall("subtoken"):
            n = Subtoken(**a.attrib)
            self.subtokens[n.id] = n
        
        # generate depTokens
        for a in tmpDep.findall("deptoken"):
            n = DepToken(**a.attrib)
            for b in a.findall("nestedsubtoken"):
                special = (b.attrib['special'] == 'True')
                n.addSubtoken( self.subtokens[b.attrib['subtoken']],special )
            self.deptokens[n.id] = n

        # generate relTokens
        for a in tmpRel.findall("reltoken"):
            n = RelToken(**a.attrib)
            for b in a.findall("nestedsubtoken"):
                special = (b.attrib['special'] == 'True')
                n.addSubtoken( self.subtokens[b.attrib['subtoken']],special )
            self.reltokens[n.id] = n
        
        # generate depEntities
        for a in tmpDep.findall("depentity"):
            n = DepEntity(**a.attrib)
            n.token = self.deptokens[n.token]
            self.depentities[n.id] = n

        # generate relEntities
        for a in tmpRel.findall("relentity"):
            n = RelEntity(**a.attrib)
            n.token = self.reltokens[n.token]
            self.relentities[n.id] = n
        
        # generate depNodes into graph
        depNodes = {}
        for a in tmpDep.findall("depnode"):
            n = DepNode(**a.attrib)
            n.entity = self.depentities[n.entity]
            self.dependencies.add_node(n)
            depNodes[n.id] = n
        # generate depEdges into graph
        for a in tmpDep.findall("depedge"):
            n = DepEdge(**a.attrib)
            n.bgn = depNodes[n.bgn]
            n.end = depNodes[n.end]
            self.dependencies.add_edge(depNodes[a.attrib['bgn']],
                                       depNodes[a.attrib['end']],
                                       n)

        # generate relNodes into graph
        relNodes = {}
        for a in tmpRel.findall("relnode"):
            n = RelNode(**a.attrib)
            n.entity = self.relentities[n.entity]
            self.interactions.add_node(n)
            relNodes[n.id] = n
        # generate relEdges into graph
        for a in tmpRel.findall("reledge"):
            n = RelEdge(**a.attrib)
            n.bgn = relNodes[n.bgn]
            n.end = relNodes[n.end]
            self.interactions.add_edge(relNodes[a.attrib['bgn']],
                                       relNodes[a.attrib['end']],
                                       n)
    
    def getNode(self):
        """
        Returns the data of the instance.

        @return: The sentence node containing the data of the instance
        @rtype: ET.Element 'sentence'
        """
        node = SimpleElement.getNode(self)
        node.tag = "sentence"
        del node.attrib['subtokens']
        del node.attrib['deptokens']
        del node.attrib['reltokens']
        del node.attrib['depentities']
        del node.attrib['relentities']
        del node.attrib['dependencies']
        del node.attrib['interactions']

        tmp = ET.Element("subtokens")
        node.append(tmp)
        v = self.subtokens.values()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        tmp = ET.Element("depannotation")
        node.append(tmp)
        v = self.deptokens.values()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.depentities.values()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.dependencies.nodes()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.dependencies.edges()
        v.sort(Sentence.sortEdge)
        for a in v:
            l = a[2].getNode()
            if not l.attrib['bgn'] == a[0].id:
                printError(self.__class__,
                           inspect.stack()[0][3],
                           "attribute 'bgn' in %s does not match with graph"%
                   (a[2].id))
            if not l.attrib['end'] == a[1].id:
                printError(self.__class__,
                           inspect.stack()[0][3],
                           "attribute 'end' in %s does not match with graph"%
                   (a[2].id))
            tmp.append(l)

        tmp = ET.Element("relannotation")
        node.append(tmp)
        v = self.reltokens.values()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.relentities.values()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.interactions.nodes()
        v.sort(Sentence.sortById)
        for a in v:
            tmp.append(a.getNode())

        v = self.interactions.edges()
        v.sort(Sentence.sortEdge)
        for a in v:
            l = a[2].getNode()
            if not l.attrib['bgn'] == a[0].id:
                printError(self.__class__,
                           inspect.stack()[0][3],
                           "attribute 'bgn' in %s does not match with graph"%
                   (a[2].id))
            if not l.attrib['end'] == a[1].id:
                printError(self.__class__,
                           inspect.stack()[0][3],
                           "attribute 'end' in %s does not match with graph"%
                   (a[2].id))
            tmp.append(l)

        return(node)

        
# ----
# validity check functions
# ----

    def isEqual(self,n1,n2):
        """
        NOT IMPLEMENTED
        """
        pass

# ----
# utility functions
# ----

    @classmethod
    def sortById(cls,x,y):
        """
        Sorting function that sorts by element id
        """
        return(x.getRunningId()-y.getRunningId())

    @classmethod
    def sortEdge(cls,x,y):
        """
        Sorting function for edges
        """
        return( Sentence.sortById(x[2],y[2]) )

# Old sorting methods

#     @classmethod
#     def sortNode(cls,x,y):
#         """
#         Sorting function for elements
#         """
#         return( Sentence.sortById(x,y) )

#     @classmethod
#     def sortEdge(cls,x,y):
#         """
#         Sorting function for edges
#         """
#         cur = Sentence.sortById(x[0].entity,y[0].entity)
#         if cur: return(cur)
#         cur = Sentence.sortById(x[0],y[0])
#         if cur: return(cur)
#         cur = Sentence.sortById(x[1].entity,y[1].entity)
#         if cur: return(cur)
#         cur = Sentence.sortById(x[1],y[1])
#         if cur: return(cur)
#         return(0)

#     @classmethod
#     def sortLink(cls,x,y):
#         """
#         Sorting function for depedges
#         """
#         if x[2].linkage>y[2].linkage:
#             return(1)
#         elif x[2].linkage<y[2].linkage:
#             return(-1)
#         return(Sentence.sortEdge(x,y))

    def DEBUG_printLeafPlams(self,writeTo):
        """
        Debugging function
        """
        G = self.interactions
        leafs = [x for x in G.nodes() if not G.out_edges(x)]
        for leaf in leafs:
            writeTo.write("%s | %s\n"%(leaf.id,
                                       self.getText(leaf)))

    def DEBUG_printLevelTexts(self,writeTo):
        """
        Debugging function
        """
        G = sentence.interactions
        nodes = [(node,x[1])
                 for node in G.nodes()
                 for x in G.out_edges(node)
                 if x[2].type=='nesting']
        for node,nested in nodes:
            all = [x.id for x in node]
            sub = [x.id for x in nested]
            level = all[:]
            for a in sub:
                level.remove(a)
            tmp1 = " ".join([self.subtokens[x].text for x in level])
            tmp2 = " ".join([self.subtokens[x].text for x in sub])
            writeTo.write("%s | %s:%s | %s | %s\n"%(node.id,
                                                    node.type,
                                                    nested.type,
                                                    tmp1,
                                                    tmp2))
