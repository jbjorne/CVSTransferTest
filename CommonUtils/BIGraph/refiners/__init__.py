"""
Refiners are manipulators of interaction graphs. They produce data
sets with different properties. CorpusRefiner is a wrapper class for
refiners that processes the whole corpus at once.

The refiners can:
  - restructure the data
  - remove unwanted details
  - produce new details

Refiners do not leave the sentence valid. Use 'pack' (in utils) and 'prune' (in Sentence-class).
"""

import sys
import inspect
from BIGraph import *

def formatRelNode(node):
    """
    Formats RelNode content for printing.

    @param node: node
    @type node: RelNode
    @return: short representation of node
    @rtype: string
    """
    return("%s (%s)"%(node.id,
                      node.entity.id))

def formatRelNodeFull(node):
    """
    Formats RelNode content for printing.

    @param node: node
    @type node: RelNode
    @return: full representation of node
    @rtype: string
    """
    return("%s (%s/%s/%s)"%(node.id,
                            node.entity.id,
                            node.entity.type,
                            node.entity.token.getText()))

def formatRelEdge(edge):
    """
    Formats RelEdge content for printing.

    @param edge: edge
    @type edge: RelEdge
    @return: full representation of edge
    @rtype: string
    """
    return("%s -- %s >> %s"%
           (edge[2].type,
            formatRelNodeFull(edge[0]),
            formatRelNodeFull(edge[1]))
           )

# collect incoming and outgoing edges by type
def collectByType(node,G):
    """
    Collects in_edges and out_edges and keys them by edge type

    @param node: node
    @type node: RelNode
    @param G: relationship graph
    @type G: networkx.XDiGraph
    @return: edges to/from node sorted by edge type
    @rtype: tuple of two dicts
    """
    inDict = {}
    for b in G.in_edges(node):
        t = b[2].type
        if not inDict.has_key(t):
            inDict[t] = set()
        inDict[t].add(b[0])

    outDict = {}
    for b in G.out_edges(node):
        t = b[2].type
        if not outDict.has_key(t):
            outDict[t] = set()
        outDict[t].add(b[1])

    return( {'in':inDict, 'out':outDict} )


class Refiner:
    """
    Superclass for interaction refiners.

    Methods resolve and remove are interface methods and must be overwritten
    by the subclasses.
    """
    def __init__(self,sentence,ontologies):
        """
        Each instance handles a single sentence.
        """
        self.sentence = sentence
        """ Sentence object """
        self.ontologies = ontologies
        """ Ontology objects in dictionary by ontology type """

    def resolve(self):
        """
        Analyses the whole interaction graph of the sentence and resolves all
        found instances. The changes are made directly into the Sentence
        object.
        """
        pass

    def remove(self):
        """
        Analyses the whole interaction graph of the sentence and removes all
        found instances. The changes are made directly into the Sentence
        object.
        """
        pass

    def removePred(self,n):
        """
        Removes the given node from the graph. Used for removing unwanted or
        obsolete linking nodes.
        """
        G = self.sentence.interactions
        G.delete_node(n)
        self.pm("node removed",formatRelNodeFull(n))
 
    def hasValidType(self,node,t):
        """
        Validity check - true if node has a given type.
        """
        if not node.entity.type==t:
            self.pe("invalid type",formatRelNodeFull(node))
            return(False)
        return(True)

    def isTop(self,node):
        """
        Validity check - true if node has no incoming edges.
        """
        G = self.sentence.interactions
        tmp = collectByType(node,G)
        if tmp['in'].keys():
            self.pe("invalid node (incoming edges)",formatRelNodeFull(node))
            return(False)
        return(True)

    def hasExactlyAgentPatient(self,node):
        """
        Validity check - true if the outgoing edges of the node are exactly
        of types 'agent' and 'patient'.
        """
        G = self.sentence.interactions
        tmp = collectByType(node,G)
        if not 'agent' in tmp['out'].keys():
            self.pe("invalid node (no agent)",formatRelNodeFull(node))
            return(False)
        if not 'patient' in tmp['out'].keys():
            self.pe("invalid node (no patient)",formatRelNodeFull(node))
            return(False)
        del tmp['out']['agent']
        del tmp['out']['patient']
        if tmp['out'].keys():
            self.pe("invalid node (extra outgoing edges -- %s)"%
                    str(tmp['out'].keys()),
                    formatRelNodeFull(node))
            return(False)
        return(True)

    def collectPairs(self,node):
        """
        Collects combinations of agent-patient leaving the node.
        """
        G = self.sentence.interactions
        oe = G.out_edges(node)
        agent = [y for (x,y,z) in oe if z.type=='agent']
        patient = [y for (x,y,z) in oe if z.type=='patient']
        return( [(x,y,node) for x in agent for y in patient] )

    def pm(self,title,target):
        printMessage(self.__class__,
                     inspect.stack()[1][3],
                     "%s in %s: %s"%(title,self.sentence.id,target))
    
    def pw(self,title,target):
        printWarning(self.__class__,
                     inspect.stack()[1][3],
                     "%s in %s: %s"%(title,self.sentence.id,target))
        
    def pe(self,title,target):
        printError(self.__class__,
                   inspect.stack()[1][3],
                   "%s in %s: %s"%(title,self.sentence.id,target))
    
class CorpusRefiner:
    """
    Wrapper class for Refiner subclasses. Processes the whole corpus at once.
    """
    def __init__(self,corpus,refiner):
        """
        @param corpus: corpus
        @type corpus: Corpus
        @param refiner: desired refiner
        @type refiner: Refiner subclass
        """
        self.corpus = corpus
        self.refiner = refiner

    def resolveAll(self):
        """
        Resolves all instances in the whole corpus.
        """
        for sentence in self.corpus.sentences:
            tmp = self.refiner(sentence,self.corpus.vocabularies)
            tmp.resolve()
            sentence.prune()

    def removeAll(self):
        """
        Removes all instances in the whole corpus.
        """
        for sentence in self.corpus.sentences:
            tmp = self.refiner(sentence,self.corpus.vocabularies)
            tmp.remove()
            sentence.prune()
