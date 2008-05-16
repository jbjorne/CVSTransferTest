import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class Anonymous(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        G = self.sentence.interactions
        anon = [x for x in G.nodes()
                if len(x.entity.token.getNested()) == 0]
        anon_roots = [x for x in anon if len(G.in_edges())==0]
        anon_nonroots = [x for x in anon if x not in anon_roots]
        
        for n in anon_nonroots+anon_roots:
            self.isValid(n) # force execution but report errors
            self.resolveAlias(n)

    def remove(self):
        self.pe("remove-method not supported","")

    def isValid(self,node):
        G = self.sentence.interactions
        # no text binding
        if len(node.entity.token.getNested()) != 0:
            self.pe("should have no text binding",formatRelNodeFull(node))
            return(False)
        # if not root, must have exactly one parent and no out edges
        if not self.isTop(node):
            if G.out_edges(node):
                self.pe("non-root with out edges",formatRelNodeFull(node))
                return(False)
            if len(G.in_edges(node)) > 1:
                self.pe("non-root with more than parent",formatRelNodeFull(node))
                return(False)
        return(True)

    def resolveAlias(self,node):
        def addEdge(a,b):
            edge = self.sentence.newElement(RelEdge)
            edge.bgn = a
            edge.end = b
            edge.type = node.entity.type
            G.add_edge(a,b,edge)
            self.pm("edge added",formatRelEdge((a,b,edge)))
            
        G = self.sentence.interactions
        if self.isTop(node):
            agents = [x[1] for x in G.out_edges(node)
                      if x[2].type=='agent']
            patients = [x[1] for x in G.out_edges(node)
                        if x[2].type=='patient']
            agpats = [x[1] for x in G.out_edges(node)
                        if x[2].type=='agpat']
            G.delete_node(node)
            self.pm("node removed",formatRelNodeFull(node))
            for a in agents:
                for b in patients:
                    addEdge(a,b)
            for a in agpats:
                for b in agpats:
                    if not a==b:
                        addEdge(a,b)
        else:
            G.delete_node(node)
            self.pm("node removed",formatRelNodeFull(node))
