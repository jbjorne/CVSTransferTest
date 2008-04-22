import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class NOT(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        def process(node,G):
            lst.remove(node)
            self.isValid(node) # force execution but report errors
            for parent in set([x for x in G.in_neighbors(node)
                               if x in lst]):
                process(parent,G) # process parent NOTs first
            self.polarise(node)

        G = self.sentence.interactions
        lst = [x for x in G.nodes()
               if x.entity.type=='NOT' and
               # exclude nodes that are already processed
               # (but only in the initial list)
               not any([y[2].type=='polarity' for y in G.in_edges(x)])]
        while lst:
            process(lst[0],G)

    def remove(self):
        G = self.sentence.interactions
        for node in [x for x in G.nodes()
                     if x.entity.type=='NOT' and
                     # exclude nodes that are already processed
                     not any([y[2].type=='polarity' for y in G.in_edges(x)])]:
            self.isValid(node) # force execution but report errors
            self.removePred(node)

    def removePred(self,node):
        G = self.sentence.interactions
        self._pull(node)
        G.delete_node(node)
        self.pm("node removed",formatRelNodeFull(node))
    
    def isValid(self,node):
        # plam type must be NOT
        if not self.hasValidType(node,"NOT"):
            return(False)
        G = self.sentence.interactions
        edges = [x for x in G.out_edges(node)
                 if not x[2].type=='polarity']
        # NOT must have exactly one outgoing edge
        if not len(edges)==1:
            self.pe("not exactly one outgoing edge (excluding 'polarity')",
                    formatRelNodeFull(node))
            return(False)
        # and its target must not have any other incoming edges
        target = edges[0][1]
        if len(G.in_edges(target))>1:
            self.pe("not exactly one incoming edge",
                    formatRelNodeFull(target))
            return(False)
        return(True)

    def polarise(self,node):
        G = self.sentence.interactions
        source,target,edge = self._pull(node)
        G.delete_edge(source,target,edge)
        edge.bgn,edge.end = edge.end,edge.bgn
        edge.type = 'polarity'
        G.add_edge(target,source,edge)
        self.pm("node relocated",formatRelNodeFull(node))

    def _pull(self,node):
        G = self.sentence.interactions
        source,target,edge = [x for x in G.out_edges(node)
                              if not x[2].type=='polarity'][0]
        for e in G.in_edges(node):
            G.delete_edge(e)
            e[2].end = target
            G.add_edge(e[0],target,e[2])
        return(source,target,edge)
